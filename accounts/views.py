# accounts/views.py
import hashlib
import secrets
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import Profile, DocumentVerification, VerificationLog, ProfileVerification, Subscription
from .forms import SignUpForm, ProfessionalSignUpForm, AccountTypeForm, ProfileEditForm, IndividuRoleForm
from django.contrib import messages
import logging
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)


class PasswordResetView(DjangoPasswordResetView):
    """Enregistre l'email utilisé pour permettre un nouveau lien après 30 secondes."""

    def form_valid(self, form):
        email = form.cleaned_data['email']
        self.request.session['password_reset_email'] = email
        return super().form_valid(form)


def send_sms(phone_number: str, message: str):
    """Envoie un SMS via le backend configuré. Par défaut, affiche dans la console pour le dev."""
    backend = getattr(settings, 'SMS_BACKEND', '')
    if not backend or backend == 'console':
        # Afficher dans la console / logs pour le développement
        logger.info(f"[SMS -> {phone_number}] {message}")
        print(f"[SMS -> {phone_number}] {message}")
        return True

    # Placeholder: intégration avec Twilio ou autre service peut être ajoutée ici
    # Si aucun backend connu n'est configuré, journaliser et échouer proprement
    logger.warning('Aucun backend SMS pris en charge n\'est configuré; message non envoyé.')
    return False


def get_file_hash(file_obj):
    """Calcule le SHA256 d'un fichier pour l'anti-fraude"""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file_obj.read(4096), b""):
        sha256_hash.update(byte_block)
    file_obj.seek(0)  # Reset file pointer
    return sha256_hash.hexdigest()


def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def inscription(request):
    # Étape 1: Choisir le type de compte
    if request.method == 'POST' and 'account_type' in request.POST:
        account_type_form = AccountTypeForm(request.POST)
        if account_type_form.is_valid():
            account_type = account_type_form.cleaned_data['account_type']
            request.session['account_type'] = account_type
            
            # Rediriger vers le formulaire spécifique
            if account_type == 'individu':
                return redirect('accounts:inscription_individu')
            elif account_type == 'residence':
                return redirect('accounts:inscription_residence')
            elif account_type == 'hotel':
                return redirect('accounts:inscription_hotel')
    
    # Afficher le formulaire de choix du type de compte
    account_type_form = AccountTypeForm()
    return render(request, 'accounts/inscription.html', {'account_type_form': account_type_form})


def inscription_individu(request):
    """Étape 1 : Choix du rôle pour les individus"""
    if request.session.get('account_type') != 'individu':
        return redirect('accounts:inscription')
    
    if request.method == 'POST':
        form = IndividuRoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            request.session['individu_role'] = role
            return redirect('accounts:inscription_individu_form')
    else:
        form = IndividuRoleForm()

    return render(request, 'accounts/inscription_individu_role.html', {'form': form})


def inscription_individu_form(request):
    """Étape 2 : Remplir le formulaire d'inscription pour les individus"""
    if request.session.get('account_type') != 'individu' or 'individu_role' not in request.session:
        return redirect('accounts:inscription')
    
    role = request.session['individu_role']
    
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            # Save user as inactive and start phone verification flow
            user = form.save(commit=True)
            user.is_active = False
            user.save(update_fields=['is_active'])

            profile = user.profile
            profile.account_type = 'individu'
            profile.role = role
            profile.verification_status = 'pending'
            profile.save(update_fields=['account_type', 'role', 'verification_status'])

            # Générer un code SMS à 6 chiffres
            code = '{:06d}'.format(secrets.randbelow(1000000))
            profile.phone_verification_code = code
            profile.phone_verification_created_at = timezone.now()
            profile.save(update_fields=['phone_verification_code', 'phone_verification_created_at'])

            # Envoyer le SMS (console fallback)
            send_sms(profile.telephone, f"Votre code Coloc.ai : {code}")

            client_ip = get_client_ip(request)
            role_label = dict(Profile.ROLE_CHOICES).get(role, role)
            VerificationLog.objects.create(
                profile=profile,
                action='created',
                details=f"Inscription (Individu - {role_label}) complétée. Code SMS envoyé au {profile.telephone}",
                ip_address=client_ip
            )

            # Conserver l'utilisateur en attente dans la session
            request.session['pending_user_id'] = user.pk

            # Nettoyer la session temporaire
            if 'account_type' in request.session:
                del request.session['account_type']
            if 'individu_role' in request.session:
                del request.session['individu_role']

            return redirect('accounts:verify_phone')
    else:
        form = SignUpForm()

    context = {
        'form': form,
        'role': role,
        'role_label': dict(Profile.ROLE_CHOICES).get(role, role),
    }
    return render(request, 'accounts/inscription_individu_form.html', context)


def inscription_pending(request):
    """Page affichée après une inscription réussie mais avant activation du compte."""
    return render(request, 'accounts/inscription_pending.html')


def resend_activation(request):
    """Permet à l'utilisateur de demander le renvoi de l'email d'activation."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "Veuillez fournir une adresse email.")
            return redirect('accounts:inscription_pending')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Aucun compte trouvé pour cette adresse email.")
            return redirect('accounts:inscription_pending')

        if user.is_active:
            messages.info(request, "Ce compte est déjà activé. Vous pouvez vous connecter.")
            return redirect('accounts:login')

        # Générer un nouveau token et envoyer l'email
        token = secrets.token_urlsafe(32)
        profile = user.profile
        profile.activation_token = token
        profile.activation_token_created_at = timezone.now()
        profile.save(update_fields=['activation_token', 'activation_token_created_at'])

        site = get_current_site(request)
        activation_link = f"http://{site.domain}/accounts/activer/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/"
        subject = 'Activation de votre compte Coloc.ai - Renvoyé'
        message = render_to_string('accounts/emails/activation_email.html', {
            'user': user,
            'activation_link': activation_link,
            'site_name': site.name,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

        messages.success(request, "Un nouvel email d'activation a été envoyé.")
        return redirect('accounts:inscription_pending')

    # GET -> afficher la page avec formulaire simple
    return render(request, 'accounts/inscription_pending.html')


def activate_account(request, uidb64, token):
    """Active un compte utilisateur à partir du lien envoyé par email."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and user.profile.activation_token == token and user.profile.activation_token_created_at:
        if timezone.now() - user.profile.activation_token_created_at > timezone.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS):
            return render(request, 'accounts/activation_expired.html')

        user.is_active = True
        user.save(update_fields=['is_active'])
        user.profile.activation_token = ''
        user.profile.activation_token_created_at = None
        user.profile.save(update_fields=['activation_token', 'activation_token_created_at'])
        return render(request, 'accounts/activation_success.html')

    return render(request, 'accounts/activation_invalid.html')


def verify_phone(request):
    """Vérifier le code envoyé par SMS pour activer le compte."""
    pending_id = request.session.get('pending_user_id')
    if not pending_id:
        return redirect('accounts:inscription')

    try:
        user = User.objects.get(pk=pending_id)
    except User.DoesNotExist:
        messages.error(request, "Compte introuvable.")
        return redirect('accounts:inscription')

    profile = user.profile

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if not code:
            messages.error(request, "Veuillez saisir le code reçu par SMS.")
            return render(request, 'accounts/verify_phone.html', {'phone': profile.telephone})

        # Vérifier expiration (15 minutes)
        if profile.phone_verification_created_at and timezone.now() - profile.phone_verification_created_at > timezone.timedelta(minutes=15):
            messages.error(request, "Le code a expiré. Demandez un nouveau code.")
            return redirect('accounts:inscription_pending')

        if code == profile.phone_verification_code:
            user.is_active = True
            user.save(update_fields=['is_active'])

            profile.phone_verified = True
            profile.phone_verification_code = ''
            profile.phone_verification_created_at = None
            profile.save(update_fields=['phone_verified', 'phone_verification_code', 'phone_verification_created_at'])

            # Nettoyer la session
            if 'pending_user_id' in request.session:
                del request.session['pending_user_id']

            login(request, user)
            messages.success(request, "Votre numéro a été vérifié et votre compte activé.")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Code invalide. Vérifiez et réessayez.")

    return render(request, 'accounts/verify_phone.html', {'phone': profile.telephone})


def resend_phone_code(request):
    """Renvoyer le code SMS pour un compte en attente."""
    if request.method != 'POST':
        return redirect('accounts:inscription_pending')

    phone = request.POST.get('phone', '').strip()
    if not phone:
        messages.error(request, "Veuillez fournir un numéro de téléphone.")
        return redirect('accounts:inscription_pending')

    try:
        profile = Profile.objects.get(telephone=phone)
        user = profile.user
    except Profile.DoesNotExist:
        messages.error(request, "Aucun compte trouvé pour ce numéro.")
        return redirect('accounts:inscription_pending')

    if user.is_active:
        messages.info(request, "Le compte lié à ce numéro est déjà activé.")
        return redirect('accounts:login')

    code = '{:06d}'.format(secrets.randbelow(1000000))
    profile.phone_verification_code = code
    profile.phone_verification_created_at = timezone.now()
    profile.save(update_fields=['phone_verification_code', 'phone_verification_created_at'])

    send_sms(profile.telephone, f"Votre nouveau code Coloc.ai : {code}")
    messages.success(request, "Un nouveau code a été envoyé par SMS.")
    # Si le compte est celui en attente, mettre à jour la session
    request.session['pending_user_id'] = user.pk
    return redirect('accounts:inscription_pending')


def inscription_residence(request):
    """Formulaire d'inscription pour les gestionnaires de résidence"""
    if request.session.get('account_type') != 'residence':
        return redirect('accounts:inscription')
    
    if request.method == 'POST':
        form = ProfessionalSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(establishment_type='residence')
            
            # Créer un log de vérification pour l'inscription
            client_ip = get_client_ip(request)
            profile = user.profile
            VerificationLog.objects.create(
                profile=profile,
                action='created',
                details=f"Inscription (Résidence) complétée. Établissement: {form.cleaned_data['establishment_name']}",
                ip_address=client_ip
            )
            
            login(request, user)
            
            # Supprimer le type de compte de la session
            if 'account_type' in request.session:
                del request.session['account_type']
            
            # Rediriger vers la page de vérification des documents
            return redirect('accounts:verification_docs')
    else:
        form = ProfessionalSignUpForm()

    return render(request, 'accounts/inscription_residence.html', {'form': form})


def inscription_hotel(request):
    """Formulaire d'inscription pour les gestionnaires d'hôtel"""
    if request.session.get('account_type') != 'hotel':
        return redirect('accounts:inscription')
    
    if request.method == 'POST':
        form = ProfessionalSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(establishment_type='hotel')
            
            # Créer un log de vérification pour l'inscription
            client_ip = get_client_ip(request)
            profile = user.profile
            VerificationLog.objects.create(
                profile=profile,
                action='created',
                details=f"Inscription (Hôtel) complétée. Établissement: {form.cleaned_data['establishment_name']}",
                ip_address=client_ip
            )
            
            login(request, user)
            
            # Supprimer le type de compte de la session
            if 'account_type' in request.session:
                del request.session['account_type']
            
            # Rediriger vers la page de vérification des documents
            return redirect('accounts:verification_docs')
    else:
        form = ProfessionalSignUpForm()

    return render(request, 'accounts/inscription_hotel.html', {'form': form})


@login_required
def verification_docs(request):
    """Page de vérification des documents"""
    profile = request.user.profile
    documents = profile.documents.all()
    
    context = {
        'profile': profile,
        'documents': documents,
        'verification_status': profile.verification_status,
    }
    return render(request, 'accounts/verification_docs.html', context)


@login_required
def verify_profile(request, user_id):
    """Permet à un utilisateur de vérifier un autre profil."""
    target_user = User.objects.filter(pk=user_id).first()
    if not target_user or target_user == request.user:
        messages.error(request, 'Impossible de vérifier ce profil.')
        return redirect('accounts:profil')

    target_profile = target_user.profile
    ProfileVerification.objects.get_or_create(verifier=request.user, verified_profile=target_profile)
    messages.success(request, f'Vous avez vérifié le profil de {target_user.get_full_name() or target_user.username}.')
    return redirect('accounts:profil')


@login_required
def upload_document(request):
    """Upload un document de vérification avec auto-approbation si complet"""
    if request.method != 'POST':
        return redirect('accounts:verification_docs')
    
    profile = request.user.profile
    document_type = request.POST.get('document_type')
    document_file = request.FILES.get('document_file')
    
    if not document_type or not document_file:
        return redirect('accounts:verification_docs')
    
    # Vérifications de sécurité
    if document_file.size > 5 * 1024 * 1024:  # 5MB max
        return redirect('accounts:verification_docs')
    
    # Accepter seulement les images
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    if document_file.content_type not in allowed_types:
        return redirect('accounts:verification_docs')
    
    # Calculer le hash du fichier
    file_hash = get_file_hash(document_file)
    
    # Vérifier si ce hash existe déjà (détection de fraude)
    if DocumentVerification.objects.filter(file_hash=file_hash).exists():
        VerificationLog.objects.create(
            profile=profile,
            action='document_uploaded',
            details=f"Tentative d'upload d'un document dupliqué ou frauduleux - Type: {document_type}",
            ip_address=get_client_ip(request)
        )
        profile.verification_status = 'flagged'
        profile.save()
        return redirect('accounts:verification_docs')
    
    # Créer ou mettre à jour le document
    doc, created = DocumentVerification.objects.get_or_create(
        profile=profile,
        document_type=document_type
    )
    doc.document_file = document_file
    doc.file_hash = file_hash
    doc.status = 'verified'  # Auto-approbation immediat pour documents valides
    doc.ip_address = get_client_ip(request)
    doc.user_agent = request.META.get('HTTP_USER_AGENT', '')
    doc.verified_by = None  # Admin peut vérifier manuellement plus tard
    doc.verified_at = timezone.now()
    doc.save()
    
    # Créer un log
    VerificationLog.objects.create(
        profile=profile,
        action='document_uploaded',
        details=f"Document téléchargé et approuvé automatiquement - Type: {document_type}",
        ip_address=get_client_ip(request)
    )
    
    # Vérifier si tous les documents requis sont uploadés et approuvés
    required_docs = ['id_front', 'id_back', 'selfie']
    uploaded_docs = profile.documents.filter(status='verified', document_type__in=required_docs).values_list('document_type', flat=True)
    uploaded_docs = list(uploaded_docs)
    
    # Si tous les documents sont présents, auto-approuver le profil
    if len(uploaded_docs) == 3 and all(doc_type in uploaded_docs for doc_type in required_docs):
        profile.verification_status = 'verified'
        profile.verified = True
        profile.verification_date = timezone.now()
        profile.save()
        
        VerificationLog.objects.create(
            profile=profile,
            action='profile_verified',
            details=f"Profil automatiquement approuvé - Tous les documents sont complets",
            ip_address=get_client_ip(request)
        )
    
    return redirect('accounts:verification_docs')


@login_required
@login_required
@login_required
def dashboard(request):
    """Redirection vers le dashboard approprié selon le type de compte"""
    try:
        profile = request.user.profile
        account_type = profile.account_type
        
        if account_type == 'individu':
            return redirect('accounts:dashboard_individu')
        elif account_type == 'residence':
            return redirect('accounts:dashboard_residence')
        elif account_type == 'hotel':
            return redirect('accounts:dashboard_hotel')
        else:
            # Par défaut, rediriger vers le profil
            return redirect('accounts:profil')
    except Exception as e:
        # Si pas de profil, rediriger vers le profil
        return redirect('accounts:profil')


@login_required
def dashboard_individu(request):
    """Dashboard pour les utilisateurs individuels"""
    profile = request.user.profile
    
    # Vérifier que l'utilisateur est bien un individu
    if profile.account_type != 'individu':
        return redirect('accounts:dashboard')
    
    # Récupérer les statistiques
    try:
        nb_logements_favoris = request.user.favoris.count()
    except Exception:
        nb_logements_favoris = 0
    
    try:
        nb_messages_non_lus = request.user.conversations.count()
    except Exception:
        nb_messages_non_lus = 0
    
    # Récupérer les annonces de l'utilisateur, y compris pour les profils tourist/locataire
    try:
        from logement.models import Logement
        mes_annonces = Logement.objects.filter(proprietaire=request.user).prefetch_related('photos').order_by('-created_at')[:5]
    except Exception:
        mes_annonces = []
    
    context = {
        'profile': profile,
        'nb_logements_favoris': nb_logements_favoris,
        'nb_messages_non_lus': nb_messages_non_lus,
        'mes_annonces': mes_annonces,
    }
    return render(request, 'accounts/dashboard_individu.html', context)


@login_required
def dashboard_residence(request):
    """Dashboard pour les gestionnaires de résidence"""
    profile = request.user.profile
    
    # Vérifier que l'utilisateur est gestionnaire de résidence
    if profile.account_type != 'residence':
        return redirect('accounts:dashboard')
    
    # Récupérer le profil professionnel
    try:
        prof_profile = profile.professionalprofile
    except:
        prof_profile = None
    
    # Récupérer les statistiques
    try:
        nb_logements = profile.user.logements.count()
    except Exception:
        nb_logements = 0
    
    # Statistiques avancées (à personnaliser selon vos modèles)
    nb_reservations = 0  # À adapter selon vos modèles
    nb_clients_actifs = 0  # À adapter selon vos modèles
    taux_occupation = 0  # À calculer selon vos données
    revenu_mois = 0  # À calculer selon vos données
    note_moyenne = 4.5  # À calculer selon les avis
    nb_avis = 0  # À adapter selon vos modèles
    logements_disponibles = nb_logements  # À adapter
    
    # Données récentes (exemples)
    recent_reservations = []  # À adapter selon vos modèles
    recent_tenants = []  # À adapter selon vos modèles
    recent_reviews = []  # À adapter selon vos modèles
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_logements': nb_logements,
        'nb_reservations': nb_reservations,
        'nb_clients_actifs': nb_clients_actifs,
        'taux_occupation': taux_occupation,
        'revenu_mois': revenu_mois,
        'note_moyenne': note_moyenne,
        'nb_avis': nb_avis,
        'logements_disponibles': logements_disponibles,
        'recent_reservations': recent_reservations,
        'recent_tenants': recent_tenants,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'accounts/dashboard_residence.html', context)


@login_required
def dashboard_hotel(request):
    """Dashboard pour les gestionnaires d'hôtel"""
    profile = request.user.profile
    
    # Vérifier que l'utilisateur est gestionnaire d'hôtel
    if profile.account_type != 'hotel':
        return redirect('accounts:dashboard')
    
    # Récupérer le profil professionnel
    try:
        prof_profile = profile.professionalprofile
    except:
        prof_profile = None
    
    # Récupérer les statistiques
    try:
        nb_chambres = profile.user.logements.count()
    except Exception:
        nb_chambres = 0
    
    # Statistiques avancées (à personnaliser selon vos modèles)
    nb_reservations = 0  # À adapter selon vos modèles
    nb_clients_actifs = 0  # À adapter selon vos modèles
    taux_occupation = 0  # À calculer selon vos données
    revenu_mois = 0  # À calculer selon vos données
    note_moyenne = 4.8  # À calculer selon les avis
    nb_avis = 0  # À adapter selon vos modèles
    chambres_disponibles = nb_chambres  # À adapter
    
    # Données récentes (exemples)
    recent_reservations = []  # À adapter selon vos modèles
    recent_clients = []  # À adapter selon vos modèles
    recent_reviews = []  # À adapter selon vos modèles
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_chambres': nb_chambres,
        'nb_reservations': nb_reservations,
        'nb_clients_actifs': nb_clients_actifs,
        'taux_occupation': taux_occupation,
        'revenu_mois': revenu_mois,
        'note_moyenne': note_moyenne,
        'nb_avis': nb_avis,
        'chambres_disponibles': chambres_disponibles,
        'recent_reservations': recent_reservations,
        'recent_clients': recent_clients,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'accounts/dashboard_hotel.html', context)


@login_required
def profil(request):
    """Affiche le profil de l'utilisateur connecté."""
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Compteurs
    try:
        nb_annonces = request.user.logements.count()
    except Exception:
        nb_annonces = 0

    try:
        nb_favoris = request.user.favoris.count()
    except Exception:
        nb_favoris = 0

    try:
        nb_messages = request.user.messages_envoyes.count()
    except Exception:
        nb_messages = 0

    current_user_has_verified_profile = False
    if request.user.is_authenticated:
        current_user_has_verified_profile = profile.has_verified_by(request.user)

    context = {
        'profile': profile,
        'nb_annonces': nb_annonces,
        'nb_favoris': nb_favoris,
        'nb_messages': nb_messages,
        'current_user_has_verified_profile': current_user_has_verified_profile,
        'viewed_user': request.user,
        'is_following': False,
        'subscriber_count': 0,
    }
    return render(request, 'accounts/profil.html', context)


@login_required
def profil_user(request, user_id):
    """Affiche le profil d'un autre utilisateur avec un bouton d'abonnement visible."""
    if request.user.id == user_id:
        return redirect('accounts:profil')

    target_user = get_object_or_404(User, pk=user_id)
    profile, created = Profile.objects.get_or_create(user=target_user)

    try:
        nb_annonces = target_user.logements.count()
    except Exception:
        nb_annonces = 0

    try:
        nb_favoris = target_user.favoris.count()
    except Exception:
        nb_favoris = 0

    try:
        nb_messages = target_user.messages_envoyes.count()
    except Exception:
        nb_messages = 0

    current_user_has_verified_profile = profile.has_verified_by(request.user)
    is_following = Subscription.objects.filter(
        subscriber=request.user,
        creator=target_user,
        is_active=True
    ).exists()
    subscriber_count = Subscription.objects.filter(creator=target_user, is_active=True).count()

    context = {
        'profile': profile,
        'nb_annonces': nb_annonces,
        'nb_favoris': nb_favoris,
        'nb_messages': nb_messages,
        'current_user_has_verified_profile': current_user_has_verified_profile,
        'viewed_user': target_user,
        'is_following': is_following,
        'subscriber_count': subscriber_count,
    }
    return render(request, 'accounts/profil.html', context)


@login_required
def edit_profil(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profil')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)

    return render(request, 'accounts/edit_profil.html', {'form': form, 'profile': profile})