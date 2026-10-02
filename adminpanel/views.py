from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from accounts.models import Profile, DocumentVerification, Notification
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
        context["items"] = items
    return context


def is_staff(user):
    return user.is_authenticated and user.is_staff


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
        verification_status="pending"
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
    items = Logement.objects.select_related('proprietaire', 'proprietaire__profile').order_by('-created_at')[:12]
    stats = {
        'total_logements': Logement.objects.count(),
        'logements_disponibles': Logement.objects.filter(available_units_for_date=None).count() if False else Logement.objects.count(),
        'logements_en_attente': 0,
    }
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'logements', 'Logements', items, stats))


@user_passes_test(is_staff)
def colocations(request):
    items = ColocationAnnonce.objects.select_related('proprietaire').order_by('-created_at')[:12]
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'colocations', 'Colocations', items, {'total_colocations': ColocationAnnonce.objects.count()}))


@user_passes_test(is_staff)
def hotels_residences(request):
    items = Etablissement.objects.order_by('-created_at')[:12]
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'hotels_residences', 'Hôtels & Résidences', items, {'total_etablissements': Etablissement.objects.count()}))


@user_passes_test(is_staff)
def reservations(request):
    items = Reservation.objects.select_related('logement', 'client_user').order_by('-created_at')[:12]
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'reservations', 'Réservations', items, {'total_reservations': Reservation.objects.count(), 'reservations_en_attente': Reservation.objects.filter(statut='pending').count()}))


@user_passes_test(is_staff)
def finance(request):
    items = Paiement.objects.select_related('reservation', 'reservation__logement').order_by('-created_at')[:12]
    revenus = (Paiement.objects.filter(statut='completed').aggregate(total=Sum('montant')).get('total') or Decimal('0'))
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'finance', 'Finance', items, {'revenus_total': revenus, 'paiements_total': Paiement.objects.count(), 'paiements_en_attente': Paiement.objects.filter(statut='pending').count()}))


@user_passes_test(is_staff)
def verifications(request):
    items = DocumentVerification.objects.select_related('profile', 'profile__user').order_by('-uploaded_at')[:50]
    documents_en_attente = DocumentVerification.objects.filter(
        status__in=['pending', 'flagged']
    ).count()
    stats = {
        'documents_en_attente': documents_en_attente,
        'profils_en_attente': Profile.objects.filter(verification_status='pending').count(),
    }
    return render(
        request,
        'adminpanel/section.html',
        _build_section_context(request, 'verifications', 'Vérifications', items, stats),
    )


@user_passes_test(is_staff)
@require_POST
def approve_document(request, document_id):
    document = get_object_or_404(DocumentVerification, pk=document_id)
    if document.status not in {'pending', 'flagged'}:
        messages.info(request, 'Ce document a déjà été traité.')
        return redirect('adminpanel:verifications')

    now = timezone.now()
    document.status = 'verified'
    document.verified_by = request.user
    document.verified_at = now
    document.save(update_fields=['status', 'verified_by', 'verified_at'])

    if document.is_complete_verification():
        profile = document.profile
        profile.verification_status = 'verified'
        profile.verified = True
        profile.verification_date = now
        profile.save(update_fields=['verification_status', 'verified', 'verification_date'])

    messages.success(request, 'Document approuvé.')
    return redirect('adminpanel:verifications')


@user_passes_test(is_staff)
@require_POST
def reject_document(request, document_id):
    document = get_object_or_404(DocumentVerification, pk=document_id)
    if document.status not in {'pending', 'flagged'}:
        messages.info(request, 'Ce document a déjà été traité.')
        return redirect('adminpanel:verifications')

    document.status = 'rejected'
    document.verified_by = request.user
    document.verified_at = timezone.now()
    if not document.rejection_reason:
        document.rejection_reason = 'Document non conforme'
    document.save(update_fields=['status', 'verified_by', 'verified_at', 'rejection_reason'])
    profile = document.profile
    profile.verification_status = 'pending'
    profile.verified = False
    profile.verification_date = None
    profile.save(update_fields=['verification_status', 'verified', 'verification_date'])
    messages.success(request, 'Document rejeté.')
    return redirect('adminpanel:verifications')


@user_passes_test(is_staff)
def avis(request):
    items = (
        AvisLogement.objects
        .select_related('logement', 'auteur')
        .order_by('-created_at')[:50]
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
        .order_by('-created_at')[:50]
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
    items = _get_recent_notifications(request.user)
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'notifications', 'Notifications', items, {'notifications_total': items.count()}))


@user_passes_test(is_staff)
def statistiques(request):
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'statistiques', 'Statistiques', [], {'total_users': User.objects.count(), 'total_logements': Logement.objects.count(), 'total_reservations': Reservation.objects.count()}))


@user_passes_test(is_staff)
def parametres(request):
    return render(request, 'adminpanel/section.html', _build_section_context(request, 'parametres', 'Paramètres', [], {'system_status': 'Opérationnel'}))


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

    # Type de compte
    account_type = request.GET.get("account_type", "").strip()

    if account_type in ["individu", "residence", "hotel"]:
        queryset = queryset.filter(
            profile__account_type=account_type
        )

    # Rôle
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