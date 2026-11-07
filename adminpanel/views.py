from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, F, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

from accounts.models import (
    DocumentVerification,
    Notification,
    Profile,
    ProfessionalProfile,
    VerificationLog,
)
from accounts.notification_service import notify_user
from logement.models import (
    AvisLogement,
    Logement,
    Etablissement,
    Reservation,
    Paiement,
    SignalementAvis,
)
from colocation.models import ColocationAnnonce


def _get_recent_notifications(user):
    return (
        Notification.objects.filter(recipient=user)
        .select_related('actor')
        .order_by('-created_at')[:8]
    )


def _build_section_context(request, section_name, title, items=None, stats=None):
    context = {
        "active_section": section_name,
        "placeholder_section": section_name,
        "section_title": title,
        "recent_notifications": _get_recent_notifications(request.user),
    }
    if stats:
        context.update(stats)
    if items is not None:
        if "page_obj" not in context:
            page_obj = Paginator(items, 25).get_page(request.GET.get("page"))
            context["page_obj"] = page_obj
            context["items"] = page_obj.object_list
        else:
            context["items"] = items
    return context


def is_staff(user):
    return user.is_authenticated and user.is_staff


def _eligible_professional_profiles():
    required_document_types = ('id_front', 'id_back', 'selfie')
    return (
        ProfessionalProfile.objects
        .filter(
            is_verified=False,
            legal_document__gt='',
            establishment_photo__gt='',
            profile__account_type__in=('hotel', 'residence'),
            profile__account_type=F('establishment_type'),
            profile__verified=True,
            profile__verification_status='verified',
        )
        .annotate(
            verified_identity_document_count=Count(
                'profile__documents__document_type',
                filter=Q(
                    profile__documents__status='verified',
                    profile__documents__document_type__in=required_document_types,
                ),
                distinct=True,
            )
        )
        .filter(verified_identity_document_count=3)
    )


@user_passes_test(is_staff)
def dashboard(request):

    # ==============================
    # UTILISATEURS
    # ==============================

    total_users = User.objects.count()

    total_profiles = Profile.objects.count()

    proprietaires = Profile.objects.filter(
        role="proprietaire"
    ).count()

    locataires = Profile.objects.filter(
        role="locataire"
    ).count()

    touristes = Profile.objects.filter(
        role="touriste"
    ).count()

    comptes_hotel = Profile.objects.filter(
        account_type="hotel"
    ).count()

    comptes_residence = Profile.objects.filter(
        account_type="residence"
    ).count()

    # ==============================
    # IMMOBILIER
    # ==============================

    total_logements = Logement.objects.count()

    logements_individuels = Logement.objects.filter(
        account_type="individu"
    ).count()

    logements_hotel = Logement.objects.filter(
        account_type="hotel"
    ).count()

    logements_residence = Logement.objects.filter(
        account_type="residence"
    ).count()

    total_colocations = ColocationAnnonce.objects.count()

    total_etablissements = Etablissement.objects.count()

    hotels = Etablissement.objects.filter(
        type_etablissement="hotel"
    ).count()

    residences = Etablissement.objects.filter(
        type_etablissement="residence"
    ).count()

    # ==============================
    # RÉSERVATIONS
    # ==============================

    total_reservations = Reservation.objects.count()

    reservations_pending = Reservation.objects.filter(
        statut="pending"
    ).count()

    reservations_confirmed = Reservation.objects.filter(
        statut="confirmed"
    ).count()

    reservations_completed = Reservation.objects.filter(
        statut="completed"
    ).count()

    reservations_cancelled = Reservation.objects.filter(
        statut="cancelled"
    ).count()

    # ==============================
    # PAIEMENTS
    # ==============================

    total_paiements = Paiement.objects.count()

    paiements_pending = Paiement.objects.filter(
        statut="pending"
    ).count()

    paiements_completed = Paiement.objects.filter(
        statut="completed"
    ).count()

    paiements_failed = Paiement.objects.filter(
        statut="failed"
    ).count()

    paiements_refunded = Paiement.objects.filter(
        statut="refunded"
    ).count()

    revenus = (
        Paiement.objects
        .filter(statut="completed")
        .aggregate(total=Sum("montant"))
        .get("total")
        or Decimal("0")
    )

    # ==============================
    # VÉRIFICATIONS
    # ==============================

    verifications_en_attente = Profile.objects.filter(
        verification_status__in=("pending", "flagged"),
        user__is_staff=False,
    ).count()

    profils_verifies = Profile.objects.filter(
        verification_status="verified"
    ).count()

    profils_rejetes = Profile.objects.filter(
        verification_status="rejected"
    ).count()

    documents_en_attente = DocumentVerification.objects.filter(
        status="pending"
    ).count()

    documents_a_revoir = DocumentVerification.objects.filter(
        status="flagged"
    ).count()
    etablissements_en_attente = ProfessionalProfile.objects.filter(
        is_verified=False,
        profile__user__is_staff=False,
    ).count()

    # ==============================
    # DONNÉES RÉCENTES
    # ==============================

    derniers_utilisateurs = (
        User.objects
        .select_related("profile")
        .order_by("-date_joined")[:6]
    )

    dernieres_reservations = (
        Reservation.objects
        .select_related("logement", "client_user")
        .order_by("-created_at")[:6]
    )

    derniers_paiements = (
        Paiement.objects
        .select_related("reservation", "reservation__logement")
        .order_by("-created_at")[:6]
    )

    recent_notifications = _get_recent_notifications(request.user)

    # ==============================
    # CONTEXTE
    # ==============================

    context = {
        # Utilisateurs
        "total_users": total_users,
        "total_profiles": total_profiles,
        "proprietaires": proprietaires,
        "locataires": locataires,
        "touristes": touristes,
        "comptes_hotel": comptes_hotel,
        "comptes_residence": comptes_residence,

        # Immobilier
        "total_logements": total_logements,
        "logements_individuels": logements_individuels,
        "logements_hotel": logements_hotel,
        "logements_residence": logements_residence,
        "total_colocations": total_colocations,
        "total_etablissements": total_etablissements,
        "hotels": hotels,
        "residences": residences,

        # Réservations
        "total_reservations": total_reservations,
        "reservations_pending": reservations_pending,
        "reservations_confirmed": reservations_confirmed,
        "reservations_completed": reservations_completed,
        "reservations_cancelled": reservations_cancelled,

        # Paiements
        "total_paiements": total_paiements,
        "paiements_pending": paiements_pending,
        "paiements_completed": paiements_completed,
        "paiements_failed": paiements_failed,
        "paiements_refunded": paiements_refunded,
        "revenus": revenus,

        # Vérifications
        "verifications_en_attente": verifications_en_attente,
        "profils_verifies": profils_verifies,
        "profils_rejetes": profils_rejetes,
        "documents_en_attente": documents_en_attente,
        "documents_a_revoir": documents_a_revoir,
        "etablissements_en_attente": etablissements_en_attente,

        # Récent
        "derniers_utilisateurs": derniers_utilisateurs,
        "dernieres_reservations": dernieres_reservations,
        "derniers_paiements": derniers_paiements,
        "recent_notifications": recent_notifications,
    }

    return render(
        request,
        "adminpanel/dashboard.html",
        context
    )
    # ==============================
# GESTION DES UTILISATEURS
# ==============================

def _dashboard_placeholder(request, section_name):
    labels = {
        "dashboard": "Dashboard",
        "users": "Utilisateurs",
        "logements": "Logements",
        "colocations": "Colocations",
        "hotels_residences": "Hôtels & Résidences",
        "reservations": "Réservations",
        "finance": "Finance",
        "verifications": "Vérifications",
        "avis": "Avis",
        "signalements": "Signalements",
        "notifications": "Notifications",
        "statistiques": "Statistiques",
        "parametres": "Paramètres",
    }
    context = {
        "active_section": section_name,
        "placeholder_section": section_name,
        "section_title": labels.get(section_name, "Gestion"),
    }
    return render(request, "adminpanel/section.html", context)


@user_passes_test(is_staff)
def logements(request):
    items = Logement.objects.select_related('proprietaire', 'proprietaire__profile').order_by('-created_at')
    stats = {
        'total_logements': Logement.objects.count(),
        'logements_individuels': Logement.objects.filter(account_type='individu').count(),
        'logements_hotels': Logement.objects.filter(account_type='hotel').count(),
        'logements_residences': Logement.objects.filter(account_type='residence').count(),
    }
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'logements', 'Logements', items, stats))


@user_passes_test(is_staff)
def colocations(request):
    items = ColocationAnnonce.objects.select_related('proprietaire', 'proprietaire__profile').order_by('-created_at')
    logement_items = Logement.objects.select_related(
        'proprietaire',
        'proprietaire__profile',
    ).filter(
        account_type='individu',
        proprietaire__profile__role__in=['locataire', 'touriste'],
    ).order_by('-created_at')
    selected_role = request.GET.get('role', 'all')
    valid_roles = {role for role, _ in Profile.ROLE_CHOICES}
    if selected_role in valid_roles:
        items = items.filter(proprietaire__profile__role=selected_role)
        logement_items = logement_items.filter(proprietaire__profile__role=selected_role)
    else:
        selected_role = 'all'

    logement_page_obj = Paginator(logement_items, 25).get_page(request.GET.get('logement_page'))
    stats = {
        'total_colocations': ColocationAnnonce.objects.count(),
        'total_recherches_logement': Logement.objects.filter(
            account_type='individu',
            proprietaire__profile__role__in=['locataire', 'touriste'],
        ).count(),
        'locataires_recherche': (
            ColocationAnnonce.objects.filter(proprietaire__profile__role='locataire').count()
            + Logement.objects.filter(
                account_type='individu',
                proprietaire__profile__role='locataire',
            ).count()
        ),
        'proprietaires_annonces': ColocationAnnonce.objects.filter(proprietaire__profile__role='proprietaire').count(),
        'touristes_recherche': (
            ColocationAnnonce.objects.filter(proprietaire__profile__role='touriste').count()
            + Logement.objects.filter(
                account_type='individu',
                proprietaire__profile__role='touriste',
            ).count()
        ),
        'selected_colocation_role': selected_role,
        'logement_items': logement_page_obj.object_list,
        'logement_page_obj': logement_page_obj,
    }
    return render(
        request,
        'adminpanel/section.html',
        _build_section_context(request, 'colocations', 'Colocations', items, stats),
    )


@user_passes_test(is_staff)
def hotels_residences(request):
    professional_profiles = ProfessionalProfile.objects.select_related(
        'profile',
        'profile__user',
    ).order_by('is_verified', '-created_at')
    selected_status = request.GET.get('statut', 'to_review')
    if selected_status == 'to_review':
        professional_profiles = professional_profiles.filter(is_verified=False)
    elif selected_status == 'verified':
        professional_profiles = professional_profiles.filter(is_verified=True)
    elif selected_status != 'all':
        selected_status = 'to_review'
        professional_profiles = professional_profiles.filter(is_verified=False)

    page_obj = Paginator(professional_profiles, 25).get_page(request.GET.get('page'))
    items = list(page_obj.object_list)
    for professional_profile in items:
        professional_profile.identity_documents_verified = (
            professional_profile.profile.verified
            and professional_profile.profile.verification_status == 'verified'
            and professional_profile.profile.has_verified_identity_documents
        )
        professional_profile.documents_present = bool(
            professional_profile.legal_document
            and professional_profile.establishment_photo
        )

    context = _build_section_context(
        request,
        'hotels_residences',
        'Vérification des hôtels et résidences',
        items,
        {
            'total_establishments': ProfessionalProfile.objects.count(),
            'establishments_to_review': ProfessionalProfile.objects.filter(is_verified=False).count(),
            'eligible_establishments': _eligible_professional_profiles().count(),
            'verified_establishments': ProfessionalProfile.objects.filter(is_verified=True).count(),
            'page_obj': page_obj,
            'selected_establishment_status': selected_status,
        },
    )
    return render(request, 'adminpanel/section.html', context)


@user_passes_test(is_staff)
def establishment_review(request, establishment_id):
    establishment = get_object_or_404(
        Etablissement.objects.select_related('proprietaire'),
        pk=establishment_id,
    )
    profile = get_object_or_404(Profile, user=establishment.proprietaire)
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
def establishment_document_file(request, establishment_id, document_kind):
    if document_kind not in {'legal_document', 'establishment_photo'}:
        raise Http404('Type de document inconnu.')
    establishment = get_object_or_404(
        Etablissement.objects.select_related('proprietaire'),
        pk=establishment_id,
    )
    profile = Profile.objects.filter(user=establishment.proprietaire).first()
    professional_profile = (
        ProfessionalProfile.objects.filter(profile=profile).first()
        if profile
        else None
    )
    if not professional_profile:
        raise Http404('Profil professionnel introuvable.')
    return _establishment_document_response(professional_profile, document_kind)


@user_passes_test(is_staff)
@require_POST
def approve_establishment(request, establishment_id):
    establishment = get_object_or_404(Etablissement, pk=establishment_id)
    profile = get_object_or_404(Profile, user=establishment.proprietaire)
    return _approve_professional_profile(request, profile)


@user_passes_test(is_staff)
@require_POST
def approve_professional_profile(request, profile_id):
    profile = get_object_or_404(Profile, pk=profile_id)
    return _approve_professional_profile(request, profile)


def _approve_professional_profile(request, profile):
    with transaction.atomic():
        profile = get_object_or_404(
            Profile.objects.select_for_update().select_related('user'),
            pk=profile.pk,
        )
        professional_profile = get_object_or_404(
            ProfessionalProfile.objects.select_for_update(),
            profile=profile,
        )
        if professional_profile.is_verified:
            messages.info(request, 'Cet établissement est déjà vérifié.')
            return _professional_review_redirect(profile)
        if (
            not profile.verified
            or profile.verification_status != 'verified'
            or not profile.has_verified_identity_documents
        ):
            messages.warning(
                request,
                'Vérifiez d’abord l’identité du gestionnaire et ses trois pièces.',
            )
            return _professional_review_redirect(profile)
        if not professional_profile.legal_document or not professional_profile.establishment_photo:
            messages.warning(
                request,
                'Le document légal et la photo de l’établissement doivent être fournis.',
            )
            return _professional_review_redirect(profile)

        professional_profile.is_verified = True
        professional_profile.verification_date = timezone.now()
        professional_profile.save(update_fields=['is_verified', 'verification_date'])
        VerificationLog.objects.create(
            profile=profile,
            action='establishment_verified',
            details=f'Établissement « {professional_profile.establishment_name} » vérifié depuis admin-ivoire.',
            performed_by=request.user,
        )

    notify_user(
        profile.user,
        'system',
        'Établissement vérifié',
        'Les documents de votre établissement ont été vérifiés. Vous pouvez maintenant publier des annonces.',
        email_subject='Votre établissement est vérifié - Ivoire Connect',
    )
    messages.success(
        request,
        'Établissement vérifié. Le gestionnaire peut maintenant publier des annonces.',
    )
    return _professional_review_redirect(profile)


def _professional_review_redirect(profile):
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
@require_POST
def approve_eligible_establishments(request):
    approved_profiles = []
    now = timezone.now()
    with transaction.atomic():
        eligible_profiles = list(
            _eligible_professional_profiles()
            .select_for_update()
            .select_related('profile__user')
            .order_by('pk')
        )
        for professional_profile in eligible_profiles:
            if not professional_profile.eligible_for_automatic_verification:
                continue

            professional_profile.is_verified = True
            professional_profile.verification_date = now
            professional_profile.save(update_fields=['is_verified', 'verification_date'])
            VerificationLog.objects.create(
                profile=professional_profile.profile,
                action='establishment_verified',
                details=(
                    f'Établissement « {professional_profile.establishment_name} » approuvé '
                    'automatiquement depuis admin-ivoire après validation de l’identité et '
                    'confirmation de la présence des fichiers légaux et de la photo. '
                    'Les fichiers n’ont pas fait l’objet d’un examen manuel.'
                ),
                performed_by=request.user,
            )
            approved_profiles.append(professional_profile)

    for professional_profile in approved_profiles:
        notify_user(
            professional_profile.profile.user,
            'system',
            'Établissement vérifié',
            (
                'Votre identité et vos pièces ont été approuvées, et les fichiers requis '
                'pour votre établissement sont présents. Vous pouvez maintenant publier '
                'des annonces.'
            ),
            email_subject='Votre établissement est vérifié - Ivoire Connect',
        )

    if approved_profiles:
        messages.success(
            request,
            f'{len(approved_profiles)} établissement(s) éligible(s) approuvé(s). '
            'Les dossiers incomplets ou dont l’identité n’est pas approuvée ont été ignorés.',
        )
    else:
        messages.info(
            request,
            'Aucun établissement complet et éligible à l’approbation automatique.',
        )
    return redirect('adminpanel:hotels_residences')


@user_passes_test(is_staff)
def reservations(request):
    items = Reservation.objects.select_related('logement', 'client_user').order_by('-created_at')
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'reservations', 'Réservations', items, {'total_reservations': Reservation.objects.count(), 'reservations_en_attente': Reservation.objects.filter(statut='pending').count()}))


@user_passes_test(is_staff)
def finance(request):
    items = Paiement.objects.select_related('reservation', 'reservation__logement').order_by('-created_at')
    revenus = (Paiement.objects.filter(statut='completed').aggregate(total=Sum('montant')).get('total') or Decimal('0'))
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'finance', 'Finance', items, {'revenus_total': revenus, 'paiements_total': Paiement.objects.count(), 'paiements_en_attente': Paiement.objects.filter(statut='pending').count()}))


@user_passes_test(is_staff)
def verifications(request):
    dossiers = (
        Profile.objects
        .filter(
            Q(verification_status__in=['pending', 'flagged'])
            | Q(
                account_type__in=['hotel', 'residence'],
                professional_profile__is_verified=False,
                professional_profile__isnull=False,
            )
        )
        .exclude(user__is_staff=True)
        .select_related('user')
        .prefetch_related('documents', 'professional_profile')
        .distinct()
        .order_by('-date_creation')
    )
    page_obj = Paginator(dossiers, 25).get_page(request.GET.get('page'))
    items = list(page_obj.object_list)
    for profile in items:
        profile.verified_required_identity_document_count = sum(
            document.status == 'verified'
            for document in profile.documents.all()
            if document.document_type in {'id_front', 'id_back', 'selfie'}
        )
    documents_en_attente = DocumentVerification.objects.filter(
        status__in=['pending', 'flagged']
    ).count()
    stats = {
        'documents_en_attente': documents_en_attente,
        'profils_en_attente': dossiers.count(),
        'etablissements_eligibles': _eligible_professional_profiles().count(),
    }
    context = _build_section_context(
        request,
        'verifications',
        'Vérifications des comptes',
        items,
        {**stats, 'page_obj': page_obj},
    )
    return render(request, 'adminpanel/section.html', context)


@user_passes_test(is_staff)
def verification_dossier(request, profile_id):
    profile = get_object_or_404(
        Profile.objects.select_related('user').prefetch_related('documents'),
        pk=profile_id,
    )
    documents_by_type = {
        document.document_type: document
        for document in profile.documents.all()
        if document.document_type in {'id_front', 'id_back', 'selfie'}
    }
    dossier_documents = [
        {
            'document_type': document_type,
            'label': dict(DocumentVerification.DOCUMENT_TYPE_CHOICES)[document_type],
            'document': documents_by_type.get(document_type),
        }
        for document_type in ('id_front', 'id_back', 'selfie')
    ]
    context = _build_section_context(
        request,
        'verification_dossier',
        f"Dossier de {profile.get_full_name() or profile.user.username}",
    )
    context.update({
        'verification_profile': profile,
        'dossier_documents': dossier_documents,
        'professional_profile': ProfessionalProfile.objects.filter(profile=profile).first(),
        'verification_logs': profile.verification_logs.select_related('performed_by')[:10],
    })
    return render(request, 'adminpanel/section.html', context)


@user_passes_test(is_staff)
def verification_establishment_document_file(request, profile_id, document_kind):
    if document_kind not in {'legal_document', 'establishment_photo'}:
        raise Http404('Type de document inconnu.')
    professional_profile = get_object_or_404(
        ProfessionalProfile.objects.select_related('profile__user'),
        profile_id=profile_id,
    )
    return _establishment_document_response(professional_profile, document_kind)


def _establishment_document_response(professional_profile, document_kind):
    document = getattr(professional_profile, document_kind, None)
    if not document or not document.name:
        raise Http404('Document introuvable.')

    file_handle = document.open('rb')
    if document_kind == 'legal_document':
        if file_handle.read(5) == b'%PDF-':
            file_handle.seek(0)
            response = FileResponse(
                file_handle,
                as_attachment=True,
                filename='document-legal.pdf',
                content_type='application/pdf',
            )
        else:
            file_handle.seek(0)
            response = _image_file_response(
                file_handle,
                'document-legal',
                as_attachment=True,
            )
    else:
        response = _image_file_response(
            file_handle,
            'photo-etablissement',
            as_attachment=False,
        )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def _image_file_response(file_handle, filename, as_attachment):
    try:
        with Image.open(file_handle) as image:
            content_type = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'GIF': 'image/gif',
            }.get(image.format)
            image.verify()
    except (Image.DecompressionBombError, OSError, UnidentifiedImageError) as error:
        file_handle.close()
        raise Http404('Le fichier image est illisible.') from error
    if not content_type:
        file_handle.close()
        raise Http404('Format d’image non pris en charge.')
    file_handle.seek(0)
    extension = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
    }[content_type]
    return FileResponse(
        file_handle,
        as_attachment=as_attachment,
        filename=f'{filename}.{extension}',
        content_type=content_type,
    )


@user_passes_test(is_staff)
def verification_document_file(request, document_id):
    document = get_object_or_404(
        DocumentVerification,
        pk=document_id,
        document_type__in=('id_front', 'id_back', 'selfie'),
    )
    file_handle = document.document_file.open('rb')
    try:
        with Image.open(file_handle) as image:
            content_type = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'GIF': 'image/gif',
            }.get(image.format)
    except (Image.DecompressionBombError, OSError, UnidentifiedImageError) as error:
        file_handle.close()
        raise Http404('Fichier de vérification illisible.') from error
    if not content_type:
        file_handle.close()
        raise Http404('Format de document non pris en charge.')

    file_handle.seek(0)
    extension = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif'}[content_type]
    response = FileResponse(
        file_handle,
        as_attachment=False,
        filename=f'{document.document_type}.{extension}',
        content_type=content_type,
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@user_passes_test(is_staff)
@require_POST
def activate_user(request, user_id):
    with transaction.atomic():
        user = get_object_or_404(User.objects.select_for_update(), pk=user_id)
        if user.is_active:
            messages.info(request, f'Le compte de {user.get_full_name() or user.username} est déjà actif.')
            return redirect('adminpanel:users')

        user.is_active = True
        user.save(update_fields=['is_active'])
        profile = Profile.objects.filter(user=user).first()
        if profile:
            VerificationLog.objects.create(
                profile=profile,
                action='account_activated',
                details='Compte activé manuellement depuis admin-ivoire.',
                performed_by=request.user,
            )

    messages.success(
        request,
        f'Le compte de {user.get_full_name() or user.username} est maintenant actif. '
        'La vérification des pièces reste indépendante.',
    )
    if profile:
        return redirect('adminpanel:verification_dossier', profile_id=profile.pk)
    return redirect('adminpanel:users')


@user_passes_test(is_staff)
@require_POST
def reject_profile(request, profile_id):
    reason = request.POST.get('rejection_reason', '').strip()
    if not reason:
        messages.error(request, 'Indiquez le motif du refus.')
        return redirect('adminpanel:verification_dossier', profile_id=profile_id)

    with transaction.atomic():
        profile = get_object_or_404(
            Profile.objects.select_for_update().select_related('user'),
            pk=profile_id,
        )
        professional_review_pending = ProfessionalProfile.objects.filter(
            profile=profile,
            is_verified=False,
        ).exists()
        if profile.verification_status == 'verified' and not professional_review_pending:
            messages.error(request, 'Une identité déjà vérifiée ne peut pas être rejetée depuis cette action.')
            return redirect('adminpanel:verification_dossier', profile_id=profile.pk)
        profile.verification_status = 'rejected'
        profile.verified = False
        profile.verification_date = None
        profile.save(update_fields=['verification_status', 'verified', 'verification_date'])
        profile.user.is_active = False
        profile.user.save(update_fields=['is_active'])
        VerificationLog.objects.create(
            profile=profile,
            action='profile_rejected',
            details=f'Inscription refusée : {reason}',
            performed_by=request.user,
        )

    notify_user(
        profile.user,
        'system',
        'Inscription refusée',
        f'Votre inscription ne peut pas être validée. Motif : {reason}',
        email_subject='Votre inscription sur Ivoire Connect',
    )
    messages.success(request, 'Inscription refusée et compte désactivé.')
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
@require_POST
def approve_document(request, document_id):
    initial_document = get_object_or_404(DocumentVerification, pk=document_id)
    should_notify_user = False
    with transaction.atomic():
        profile = get_object_or_404(
            Profile.objects.select_for_update().select_related('user'),
            pk=initial_document.profile_id,
        )
        document = get_object_or_404(
            DocumentVerification.objects.select_for_update(),
            pk=document_id,
            profile=profile,
        )
        if document.status not in {'pending', 'flagged'}:
            messages.info(request, 'Ce document a déjà été traité.')
            return redirect('adminpanel:verification_dossier', profile_id=profile.pk)

        if not profile.has_required_identity_documents:
            received_count = profile.uploaded_required_identity_document_count
            messages.warning(
                request,
                f'Approbation impossible : les 3 pièces doivent être téléversées avant le début de la vérification '
                f'({received_count}/3 reçues).',
            )
            return redirect('adminpanel:verification_dossier', profile_id=profile.pk)

        now = timezone.now()
        document.status = 'verified'
        document.verified_by = request.user
        document.verified_at = now
        admin_notes = request.POST.get('admin_notes', '').strip()
        if admin_notes:
            document.admin_notes = admin_notes
        document.save(update_fields=['status', 'verified_by', 'verified_at', 'admin_notes'])
        VerificationLog.objects.create(
            profile=profile,
            action='document_verified',
            details=f'{document.get_document_type_display()} approuvé par {request.user.username}.',
            performed_by=request.user,
        )

        if document.is_complete_verification():
            should_notify_user = not profile.verified or profile.verification_status != 'verified'
            profile.verification_status = 'verified'
            profile.verified = True
            profile.verification_date = now
            profile.save(update_fields=['verification_status', 'verified', 'verification_date'])
            messages.success(request, 'Les trois pièces sont approuvées. Le profil est maintenant vérifié.')
        else:
            approved_count = profile.documents.filter(
                status='verified',
                document_type__in=['id_front', 'id_back', 'selfie'],
            ).count()
            messages.success(
                request,
                f'Document approuvé. Le profil restera en attente jusqu’à l’approbation des 3 pièces '
                f'({approved_count}/3 approuvées).',
            )

    if should_notify_user:
        message = (
            'Vos trois pièces d’identité ont été vérifiées par notre équipe. '
            'Votre identité est maintenant validée.'
        )
        if profile.account_type in {'hotel', 'residence'}:
            message += ' La publication reste soumise à la vérification de votre établissement.'
        notify_user(
            profile.user,
            'system',
            'Identité vérifiée',
            message,
            email_subject='Votre identité est vérifiée - Ivoire Connect',
        )
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
@require_POST
def reject_document(request, document_id):
    reason = request.POST.get('rejection_reason', '').strip() or 'Document non conforme'
    initial_document = get_object_or_404(DocumentVerification, pk=document_id)
    with transaction.atomic():
        profile = get_object_or_404(
            Profile.objects.select_for_update().select_related('user'),
            pk=initial_document.profile_id,
        )
        document = get_object_or_404(
            DocumentVerification.objects.select_for_update(),
            pk=document_id,
            profile=profile,
        )
        if document.status not in {'pending', 'flagged'}:
            messages.info(request, 'Ce document a déjà été traité.')
            return redirect('adminpanel:verification_dossier', profile_id=profile.pk)

        document.status = 'rejected'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.rejection_reason = reason[:255]
        admin_notes = request.POST.get('admin_notes', '').strip()
        if admin_notes:
            document.admin_notes = admin_notes
        document.save(update_fields=[
            'status', 'verified_by', 'verified_at', 'rejection_reason', 'admin_notes',
        ])
        profile.verification_status = 'pending'
        profile.verified = False
        profile.verification_date = None
        profile.save(update_fields=['verification_status', 'verified', 'verification_date'])
        VerificationLog.objects.create(
            profile=profile,
            action='document_rejected',
            details=f'{document.get_document_type_display()} rejeté : {document.rejection_reason}',
            performed_by=request.user,
        )

    notify_user(
        profile.user,
        'system',
        'Document à corriger',
        f'Votre document « {document.get_document_type_display()} » doit être remplacé. Motif : {reason}',
        email_subject='Un document doit être corrigé - Ivoire Connect',
    )
    messages.success(request, 'Document rejeté.')
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
@require_POST
def flag_document(request, document_id):
    initial_document = get_object_or_404(DocumentVerification, pk=document_id)
    note = request.POST.get('admin_notes', '').strip()
    if not note:
        messages.error(request, 'Ajoutez une note expliquant pourquoi ce document doit être revu.')
        return redirect('adminpanel:verification_dossier', profile_id=initial_document.profile_id)

    with transaction.atomic():
        profile = get_object_or_404(
            Profile.objects.select_for_update(),
            pk=initial_document.profile_id,
        )
        document = get_object_or_404(
            DocumentVerification.objects.select_for_update(),
            pk=document_id,
            profile=profile,
        )
        if document.status not in {'pending', 'flagged'}:
            messages.info(request, 'Ce document a déjà été traité.')
            return redirect('adminpanel:verification_dossier', profile_id=profile.pk)

        document.status = 'flagged'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.admin_notes = note
        document.save(update_fields=['status', 'verified_by', 'verified_at', 'admin_notes'])
        VerificationLog.objects.create(
            profile=profile,
            action='profile_flagged',
            details=f'{document.get_document_type_display()} signalé pour revue : {note}',
            performed_by=request.user,
        )
    messages.success(request, 'Document marqué « à revoir ».')
    return redirect('adminpanel:verification_dossier', profile_id=profile.pk)


@user_passes_test(is_staff)
def avis(request):
    items = (
        AvisLogement.objects
        .select_related('logement', 'auteur')
        .order_by('-created_at')
    )
    stats = {
        'avis_total': AvisLogement.objects.count(),
        'avis_masques': AvisLogement.objects.filter(est_visible=False).count(),
    }
    return render(
        request,
        'adminpanel/section.html',
        _build_section_context(request, 'avis', 'Avis', items, stats),
    )


@user_passes_test(is_staff)
def signalements(request):
    items = (
        SignalementAvis.objects
        .select_related('avis', 'avis__logement', 'auteur')
        .order_by('-created_at')
    )
    stats = {
        'signalements_total': SignalementAvis.objects.count(),
        'signalements_a_traiter': SignalementAvis.objects.filter(traite=False).count(),
    }
    return render(
        request,
        'adminpanel/section.html',
        _build_section_context(request, 'signalements', 'Signalements', items, stats),
    )


@user_passes_test(is_staff)
@require_POST
def toggle_avis_visibility(request, avis_id):
    avis_item = get_object_or_404(AvisLogement, pk=avis_id)
    avis_item.est_visible = not avis_item.est_visible
    avis_item.save(update_fields=['est_visible', 'updated_at'])
    messages.success(
        request,
        'Avis masqué.' if not avis_item.est_visible else 'Avis rendu visible.',
    )
    return redirect('adminpanel:avis')


@user_passes_test(is_staff)
@require_POST
def traiter_signalement(request, signalement_id):
    signalement = get_object_or_404(SignalementAvis, pk=signalement_id)
    if not signalement.traite:
        signalement.traite = True
        signalement.save(update_fields=['traite'])
        messages.success(request, 'Signalement marqué comme traité.')
    else:
        messages.info(request, 'Ce signalement est déjà traité.')
    return redirect('adminpanel:signalements')


@user_passes_test(is_staff)
def notifications(request):
    items = Notification.objects.filter(recipient=request.user).select_related('actor').order_by('-created_at')
    stats = {
        'notifications_total': items.count(),
        'notifications_non_lues': items.filter(is_read=False).count(),
    }
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'notifications', 'Notifications', items, stats))


@user_passes_test(is_staff)
def statistiques(request):
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'statistiques', 'Statistiques', [], {
        'total_users': User.objects.count(),
        'total_logements': Logement.objects.count(),
        'total_colocations': ColocationAnnonce.objects.count(),
        'total_reservations': Reservation.objects.count(),
        'total_paiements': Paiement.objects.count(),
        'total_avis': AvisLogement.objects.count(),
        'total_signalements': SignalementAvis.objects.count(),
    }))


@user_passes_test(is_staff)
def parametres(request):
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'parametres', 'Paramètres', [], {
        'system_status': 'Opérationnel',
        'total_users': User.objects.count(),
        'total_logements': Logement.objects.count(),
        'total_reservations': Reservation.objects.count(),
    }))


@user_passes_test(is_staff)
def users(request):

    queryset = (
        User.objects
        .select_related("profile")
        .order_by("-date_joined")
    )

    # Recherche
    search = request.GET.get("q", "").strip()

    if search:
        queryset = queryset.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(profile__telephone__icontains=search)
        )

    # Catégories affichées à l'administration : type professionnel ou rôle individuel.
    account_type = request.GET.get("account_type", "").strip()

    account_categories = {"hotel", "residence", "proprietaire", "locataire", "touriste"}
    if account_type in {"hotel", "residence"}:
        queryset = queryset.filter(profile__account_type=account_type)
    elif account_type in {"proprietaire", "locataire", "touriste"}:
        queryset = queryset.filter(
            profile__account_type="individu",
            profile__role=account_type,
        )
    elif account_type == "individu":
        queryset = queryset.filter(profile__account_type="individu")
    elif account_type not in account_categories:
        account_type = ""

    # Compatibilité avec les anciens liens contenant encore un paramètre role.
    role = request.GET.get("role", "").strip()

    if role in ["locataire", "touriste", "proprietaire"]:
        queryset = queryset.filter(
            profile__role=role
        )

    # Statut
    status = request.GET.get("status", "").strip()

    if status == "active":
        queryset = queryset.filter(is_active=True)

    elif status == "inactive":
        queryset = queryset.filter(is_active=False)

    elif status == "verified":
        queryset = queryset.filter(
            profile__verification_status="verified"
        )

    elif status == "pending":
        queryset = queryset.filter(
            profile__verification_status="pending"
        )

    elif status == "rejected":
        queryset = queryset.filter(
            profile__verification_status="rejected"
        )

    elif status == "flagged":
        queryset = queryset.filter(
            profile__verification_status="flagged"
        )

    # Pagination
    paginator = Paginator(queryset, 15)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    # Statistiques
    total_users = User.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    inactive_users = User.objects.filter(
        is_active=False
    ).count()

    verified_users = Profile.objects.filter(
        verification_status="verified"
    ).count()

    pending_users = Profile.objects.filter(
        verification_status="pending"
    ).count()

    context = {
        "users": page_obj,
        "page_obj": page_obj,

        "search": search,
        "account_type": account_type,
        "role": role,
        "status": status,

        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "verified_users": verified_users,
        "pending_users": pending_users,
    }

    return render(
        request,
        "adminpanel/utilisateurs.html",
        context
    )