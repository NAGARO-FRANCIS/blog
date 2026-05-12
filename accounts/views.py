# accounts/views.py
import hashlib
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from .models import Profile, DocumentVerification, VerificationLog
from .forms import SignUpForm, ProfessionalSignUpForm, AccountTypeForm, ProfileEditForm


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
    """Formulaire d'inscription pour les individus"""
    if request.session.get('account_type') != 'individu':
        return redirect('accounts:inscription')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Sauvegarder les champs du profil
            profile, created = Profile.objects.get_or_create(user=user)
            profile.telephone = form.cleaned_data.get('telephone', '')
            profile.ville = form.cleaned_data.get('ville', '')
            profile.quartier = form.cleaned_data.get('quartier', '')
            profile.profession = form.cleaned_data.get('profession', '')
            profile.date_naissance = form.cleaned_data.get('date_naissance')
            profile.sexe = form.cleaned_data.get('sexe', '')
            profile.role = form.cleaned_data.get('role', '')
            profile.account_type = 'individu'
            profile.type_piece_identite = form.cleaned_data.get('type_piece_identite', '')
            profile.numero_piece_identite = form.cleaned_data.get('numero_piece_identite', '')
            profile.verification_status = 'pending'
            
            if 'photo_profil' in request.FILES:
                profile.photo_profil = request.FILES['photo_profil']
            
            profile.save()
            
            # Créer un log de vérification pour l'inscription
            client_ip = get_client_ip(request)
            VerificationLog.objects.create(
                profile=profile,
                action='created',
                details=f"Inscription (Individu) complétée. Pièce: {profile.type_piece_identite}, Numéro: {profile.numero_piece_identite}",
                ip_address=client_ip
            )
            
            login(request, user)
            
            # Supprimer le type de compte de la session
            if 'account_type' in request.session:
                del request.session['account_type']
            
            # Rediriger vers la page de vérification des documents
            return redirect('accounts:verification_docs')
    else:
        form = SignUpForm()

    return render(request, 'accounts/inscription_individu.html', {'form': form})


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
def dashboard(request):
    """Redirection vers le dashboard approprié selon le type de compte"""
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
    
    context = {
        'profile': profile,
        'nb_logements_favoris': nb_logements_favoris,
        'nb_messages_non_lus': nb_messages_non_lus,
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
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_logements': nb_logements,
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
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_chambres': nb_chambres,
    }
    return render(request, 'accounts/dashboard_hotel.html', context)


@login_required
def profil(request):
    """Affiche le profil de l'utilisateur"""
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

    context = {
        'profile': profile,
        'nb_annonces': nb_annonces,
        'nb_favoris': nb_favoris,
        'nb_messages': nb_messages,
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