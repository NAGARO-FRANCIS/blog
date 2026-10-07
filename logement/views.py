import calendar as calendar_module
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import (
    LogementProprietaireForm, LogementTouristeForm, LogementHotelForm, LogementResidenceForm,
    BlocageCalendrierForm, RechercheLogementForm, PhotoLogementFormSet, VideoLogementFormSet,
)
from .models import (
    BlocageCalendrier, Etablissement, FavoriLogement, Logement, PhotoLogement, Reservation,
    VideoLogement, Paiement, AvisLogement,
)


def _apply_logement_filters(logements, cleaned_data):
    """Applique les filtres de recherche directement à la requête SQL."""
    q = cleaned_data.get('q')
    if q:
        logements = logements.filter(
            Q(titre__icontains=q) |
            Q(description__icontains=q) |
            Q(ville__icontains=q) |
            Q(commune__icontains=q) |
            Q(quartier__icontains=q)
        )

    for field in ('ville', 'commune', 'quartier'):
        value = cleaned_data.get(field)
        if value:
            logements = logements.filter(**{f'{field}__icontains': value})

    price_fields = ('prix', 'prix_par_nuit', 'prix_par_mois')
    prix_min = cleaned_data.get('prix_min')
    prix_max = cleaned_data.get('prix_max')
    if prix_min is not None:
        logements = logements.filter(
            Q(prix__gte=prix_min) | Q(prix_par_nuit__gte=prix_min) | Q(prix_par_mois__gte=prix_min)
        )
    if prix_max is not None:
        logements = logements.filter(
            Q(prix__lte=prix_max) | Q(prix_par_nuit__lte=prix_max) | Q(prix_par_mois__lte=prix_max)
        )

    type_logement = cleaned_data.get('type_logement')
    if type_logement:
        logements = logements.filter(type_logement=type_logement)
    account_type = cleaned_data.get('account_type')
    if account_type:
        logements = logements.filter(account_type=account_type)
    chambres_min = cleaned_data.get('nombre_chambres_min')
    if chambres_min is not None:
        logements = logements.filter(nombre_chambres__gte=chambres_min)

    for field in ('meuble', 'wifi', 'garage', 'climatisation', 'securite', 'eau', 'electricite'):
        value = cleaned_data.get(field)
        if value in ('0', '1'):
            logements = logements.filter(**{field: value == '1'})

    if cleaned_data.get('disponible_immediatement'):
        logements = logements.filter(disponible_depuis__lte=date.today())
    distance_universite_max = cleaned_data.get('distance_universite_max')
    if distance_universite_max is not None:
        logements = logements.filter(distance_universite__lte=distance_universite_max)
    distance_hopital_max = cleaned_data.get('distance_hopital_max')
    if distance_hopital_max is not None:
        logements = logements.filter(distance_hopital__lte=distance_hopital_max)

    return logements.distinct()


def _map_items(logements):
    return [
        {
            'id': logement.id,
            'title': logement.titre,
            'lat': float(logement.latitude),
            'lng': float(logement.longitude),
            'url': f'/logement/{logement.id}/',
        }
        for logement in logements
        if logement.latitude is not None and logement.longitude is not None
    ]


@login_required
def choisir_type_annonce(request):
    """Affiche la page de sélection du type d'annonce"""
    return render(request, 'logement/choisir_type_annonce.html')


def home(request):
    """Page d'accueil avec annonces filtrées selon le rôle"""
    form = RechercheLogementForm(request.GET or None)
    
    # Récupérer les favoris
    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(FavoriLogement.objects.filter(utilisateur=request.user).values_list('logement_id', flat=True))

    if request.user.is_authenticated:
        try:
            profile      = request.user.profile
            role         = profile.role
            account_type = profile.account_type
        except Exception:
            role         = None
            account_type = None

        if account_type in ['hotel', 'residence']:
            # Hôtel / Résidence → voient tout
            logements = Logement.objects.all()
            is_tourist = False

        elif role == 'touriste':
            # Touriste → voit hôtels, résidences, propriétaires ET locataires
            # mais voit aussi ses propres annonces s'il en publie
            logements = Logement.objects.filter(
                Q(proprietaire=request.user) |
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role__in=['proprietaire', 'locataire']))
            )
            is_tourist = True

        elif role == 'locataire':
            # Locataire → voit hôtels, résidences, propriétaires individuels
            # mais voit aussi ses propres annonces s'il en publie
            logements = Logement.objects.filter(
                Q(proprietaire=request.user) |
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            )
            is_tourist = False

        elif role == 'proprietaire':
            # Propriétaire → voit hôtels, résidences ET autres propriétaires individuels
            # mais voit aussi ses propres annonces
            logements = Logement.objects.filter(
                Q(proprietaire=request.user) |
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            )
            is_tourist = False

        else:
            logements = Logement.objects.all()
            is_tourist = False

    else:
        # Non connecté → voit tout
        logements = Logement.objects.all()
        is_tourist = False

    if form.is_valid():
        logements = _apply_logement_filters(logements, form.cleaned_data)

    logements = logements.prefetch_related('photos').order_by('-created_at')
    map_items = _map_items(logements)

    # ── GROUPER LES ANNONCES POUR LES TOURISTES EN 4 CATÉGORIES ─────────────
    if is_tourist:
        hotels = [l for l in logements if l.account_type == 'hotel']
        residences = [l for l in logements if l.account_type == 'residence']
        locataires = [l for l in logements if l.account_type == 'individu' and l.proprietaire and l.proprietaire.profile.role == 'locataire']
        proprietaires = [l for l in logements if l.account_type == 'individu' and l.proprietaire and l.proprietaire.profile.role == 'proprietaire']
        
        context = {
            'form': form,
            'is_tourist': True,
            'annonces': list(logements),
            'hotels': hotels,
            'residences': residences,
            'locataires': locataires,
            'proprietaires': proprietaires,
            'favoris_ids': favoris_ids,
            'user_type': 'touriste',
            'map_items': map_items,
        }
    else:
        context = {
            'form': form,
            'logements': logements,
            'annonces': logements,  # Pour compatibilité avec le template
            'favoris_ids': favoris_ids,
            'user_type': request.user.profile.account_type if request.user.is_authenticated else 'anonymous',
            'is_tourist': False,
            'map_items': map_items,
        }

    return render(request, 'acceuil.html', context)


@require_http_methods(["GET"])
def listings_all_types(request):
    """Page professionnelle affichant tous les types de propriétés distincts"""

    hotels     = Logement.objects.filter(account_type='hotel').prefetch_related('photos').order_by('-created_at')
    residences = Logement.objects.filter(account_type='residence').prefetch_related('photos').order_by('-created_at')
    individuals = Logement.objects.filter(account_type='individu').prefetch_related('photos').order_by('-created_at')

    form = RechercheLogementForm(request.GET or None)
    if form.is_valid():
        hotels = _apply_logement_filters(hotels, form.cleaned_data)
        residences = _apply_logement_filters(residences, form.cleaned_data)
        individuals = _apply_logement_filters(individuals, form.cleaned_data)

    context = {
        'form':             form,
        'hotels':           hotels,
        'residences':       residences,
        'individuals':      individuals,
        'hotel_count':      len(hotels)      if isinstance(hotels,      list) else hotels.count(),
        'residence_count':  len(residences)  if isinstance(residences,  list) else residences.count(),
        'individu_count':   len(individuals) if isinstance(individuals, list) else individuals.count(),
        'total_count':     (len(hotels)      if isinstance(hotels,      list) else hotels.count()) +
                           (len(residences)  if isinstance(residences,  list) else residences.count()) +
                           (len(individuals) if isinstance(individuals, list) else individuals.count()),
    }

    return render(request, 'logement/listings_all_types.html', context)


@require_http_methods(["GET"])
def detail_logement(request, id):
    """Page de détail d'un logement"""
    from .models import FavoriLogement
    
    logement = get_object_or_404(Logement, id=id)
    photos   = logement.photos.all()
    videos   = logement.videos.all()
    reservations_count = logement.reservations.filter(statut='confirmed').count()
    
    # Vérifier si le logement est dans les favoris de l'utilisateur
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriLogement.objects.filter(
            utilisateur=request.user,
            logement=logement
        ).exists()

    context = {
        'logement':           logement,
        'photos':             photos,
        'videos':             videos,
        'reservations_count': reservations_count,
        'is_favorite':        is_favorite,
        'etablissement':      logement.etablissement,
        'etablissement_categories': (
            logement.etablissement.categories.exclude(id=logement.id)
            if logement.etablissement else []
        ),
    }

    return render(request, 'logement/detail_logement.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_favori(request, id):
    """Toggle un logement en favoris (AJAX)"""
    from .models import FavoriLogement
    
    logement = get_object_or_404(Logement, id=id)
    favori, created = FavoriLogement.objects.get_or_create(
        utilisateur=request.user,
        logement=logement,
    )
    
    if not created:
        favori.delete()
        is_favorite = False
    else:
        is_favorite = True
        from accounts.notification_service import favorite_added
        favorite_added(favori)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_favorite})
    return redirect('logement:home')


@login_required
@require_http_methods(["GET"])
def mes_favoris(request):
    """Afficher les favoris de l'utilisateur"""
    from .models import FavoriLogement
    
    favoris = FavoriLogement.objects.filter(utilisateur=request.user).select_related('logement').prefetch_related('logement__photos')
    
    context = {
        'favoris': favoris,
    }
    
    return render(request, 'logement/mes_favoris.html', context)


def _can_access_reservation(request, reservation):
    if reservation.client_user_id is not None:
        return request.user.is_authenticated and reservation.client_user_id == request.user.id
    guest_reservation_ids = request.session.get('guest_reservation_ids', [])
    return str(reservation.pk) in {str(reservation_id) for reservation_id in guest_reservation_ids}


@require_http_methods(["GET", "POST"])
def reserver_logement(request, id):
    """Créer une réservation (pour hôtels et résidences)"""
    from django.contrib import messages
    
    logement = get_object_or_404(Logement, id=id)

    if request.user.is_authenticated and logement.proprietaire_id == request.user.id:
        messages.error(
            request,
            _('❌ Vous ne pouvez pas réserver votre propre annonce.')
        )
        return redirect('logement:detail_logement', id=logement.id)

    if logement.account_type not in ['hotel', 'residence']:
        messages.error(
            request, 
            _('❌ Les annonces particulières ne sont pas réservables en ligne. '
              'Veuillez contacter directement le propriétaire.')
        )
        return redirect('logement:detail_logement', id=logement.id)

    if request.method == 'POST':
        from .forms import ReservationForm
        form = ReservationForm(request.POST, logement=logement)

        if form.is_valid():
            reservation          = form.save(commit=False)
            reservation.logement = logement
            
            # Les anciennes annonces peuvent encore stocker leur tarif dans `prix`.
            reservation.prix_par_nuit = logement.prix_par_nuit or logement.prix or 0
            if logement.frais_nettoyage:
                reservation.frais_nettoyage_reservation = logement.frais_nettoyage
            
            if request.user.is_authenticated:
                reservation.client_user  = request.user
                reservation.client_nom   = request.user.get_full_name() or request.user.username
                reservation.client_email = request.user.email

            with transaction.atomic():
                locked_logement = Logement.objects.select_for_update().get(pk=logement.pk)
                requested_units = reservation.nombre_chambres or 1
                available_units = list(
                    locked_logement.available_units_for_period(
                        reservation.date_arrivee,
                        reservation.date_depart,
                    )[:requested_units]
                )
                if len(available_units) < requested_units:
                    form.add_error(
                        None,
                        'Les chambres demandées ne sont plus disponibles pour ces dates.',
                    )
                else:
                    reservation.logement = locked_logement
                    reservation.save()
                    reservation.unites.set(available_units)

            if reservation.pk is None:
                return render(request, 'logement/reserver_logement.html', {
                    'logement': logement,
                    'form': form,
                })
            if not request.user.is_authenticated:
                guest_reservation_ids = request.session.get('guest_reservation_ids', [])
                guest_reservation_ids.append(reservation.pk)
                request.session['guest_reservation_ids'] = guest_reservation_ids[-20:]
            from accounts.notification_service import reservation_created
            reservation_created(reservation)
            return redirect('logement:paiement', reservation_id=reservation.id)
    else:
        from .forms import ReservationForm
        form = ReservationForm(logement=logement)

    return render(request, 'logement/reserver_logement.html', {
        'logement': logement,
        'form':     form,
    })


@require_http_methods(["GET", "POST"])
def paiement_reservation(request, reservation_id):
    """Page de paiement avec support multi-méthodes (MOUV, Orange Money, Wave, Stripe, Virement, Cash)"""
    from .models import Reservation, Paiement
    import importlib
    import os
    import json
    from django.http import JsonResponse
    from django.contrib import messages

    stripe = None
    try:
        stripe_spec = importlib.util.find_spec('stripe')
        if stripe_spec is not None:
            stripe = importlib.import_module('stripe')
    except Exception:
        stripe = None
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if not _can_access_reservation(request, reservation):
        if request.method == 'POST':
            return JsonResponse({
                'success': False,
                'message': 'Vous n\'êtes pas autorisé à payer cette réservation.'
            }, status=403)
        return redirect('accounts:login' if not request.user.is_authenticated else 'logement:home')

    if stripe is not None:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

    # Traitement POST (traitement du paiement)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'stripe')
        
        # Créer ou mettre à jour le paiement
        try:
            paiement, created = Paiement.objects.get_or_create(
                reservation=reservation,
                defaults={
                    'montant': reservation.montant_final,
                    'methode': payment_method,
                    'statut': 'pending'
                }
            )

            if not created:
                paiement.methode = payment_method
                paiement.save()
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de préparer le paiement: {str(e)}'
            }, status=500)
        
        # Traiter selon la méthode
        try:
            if payment_method in ('mobile_money', 'mouv', 'orange', 'wave'):
                # Mobile Money (Orange, MTN, Moov, Wave) via la page sécurisée CinetPay
                import logging
                from cinetpay import CinetPayError
                from .cinetpay_paiement import CinetPayNonConfigure, initier_paiement

                if paiement.statut == 'completed':
                    return JsonResponse({
                        'success': True,
                        'message': _('Cette réservation est déjà payée.'),
                        'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                    })
                try:
                    url_paiement = initier_paiement(paiement)
                except CinetPayNonConfigure:
                    return JsonResponse({
                        'success': False,
                        'message': _("Le paiement en ligne n'est pas encore configuré.")
                    }, status=503)
                except CinetPayError:
                    logging.getLogger(__name__).exception('CinetPay : initialisation impossible')
                    return JsonResponse({
                        'success': False,
                        'message': _("Impossible d'initialiser le paiement. Réessayez dans un instant.")
                    }, status=502)
                return JsonResponse({
                    'success': True,
                    'message': _('Redirection vers la page de paiement sécurisée...'),
                    'redirect_url': url_paiement
                })

            elif payment_method == 'mouv_ancien':
                # Ancien code MOUV (désormais inutilisé)
                mouv_number = request.POST.get('mouv_number', '')
                if not mouv_number:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez entrer votre numéro MOUV'
                    })
                
                paiement.statut = 'pending'
                paiement.description = f"MOUV: {mouv_number}"
                paiement.save()
                
                messages.success(request, _('✅ Paiement MOUV en cours de traitement. Veuillez confirmer sur votre téléphone.'))
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement MOUV en cours...',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            elif payment_method == 'orange':
                # Orange Money
                orange_number = request.POST.get('orange_number', '')
                if not orange_number:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez entrer votre numéro Orange'
                    })
                
                paiement.statut = 'pending'
                paiement.description = f"Orange Money: {orange_number}"
                paiement.save()
                
                messages.success(request, _('✅ Paiement Orange Money en cours de traitement.'))
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement Orange Money en cours...',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            elif payment_method == 'wave':
                # Wave
                wave_number = request.POST.get('wave_number', '')
                if not wave_number:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez entrer votre numéro Wave'
                    })
                
                paiement.statut = 'pending'
                paiement.description = f"Wave: {wave_number}"
                paiement.save()
                
                messages.success(request, _('✅ Paiement Wave en cours de traitement.'))
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement Wave en cours...',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            elif payment_method == 'stripe':
                # Carte bancaire via Stripe
                paiement.statut = 'pending'
                paiement.save()
                
                # TODO: Implémenter la création du PaymentIntent Stripe
                messages.info(request, _('💳 Paiement par carte bancaire en cours...'))
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement Stripe en cours...',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            elif payment_method == 'virement':
                # Virement bancaire
                paiement.statut = 'pending'
                paiement.description = f"En attente du virement bancaire"
                paiement.save()
                
                # Envoyer email avec coordonnées bancaires
                messages.info(request, _('🏦 Nos coordonnées bancaires ont été envoyées par email.'))
                return JsonResponse({
                    'success': True,
                    'message': 'Coordonnées bancaires envoyées par email',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            elif payment_method == 'cash':
                # Paiement à l'arrivée
                paiement.statut = 'pending'
                paiement.description = f"Paiement à l'arrivée"
                paiement.save()
                
                # Marquer la réservation comme confirmée en attente
                reservation.statut = 'confirmed'
                reservation.save()
                from accounts.notification_service import reservation_confirmed
                reservation_confirmed(reservation)
                
                messages.success(request, _('✅ Réservation confirmée. Paiement à l\'arrivée.'))
                return JsonResponse({
                    'success': True,
                    'message': 'Réservation confirmée',
                    'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Méthode de paiement non reconnue'
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du traitement: {str(e)}'
            })
    
    # GET - Afficher la page de paiement
    context = {
        'reservation': reservation,
        'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY', ''),
    }
    
    return render(request, 'logement/paiement_reservation.html', context)


@require_http_methods(["GET"])
def confirmation_reservation(request, reservation_id):
    """Page de confirmation de réservation"""
    from .models import Reservation
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if not _can_access_reservation(request, reservation):
        return redirect('accounts:login' if not request.user.is_authenticated else 'logement:home')
    
    context = {
        'reservation': reservation,
    }
    
    return render(request, 'logement/confirmation_reservation.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def ajouter_logement(request):
    """Ajouter un logement — formulaire différencié selon le type de compte"""

    try:
        profile      = request.user.profile
        account_type = profile.account_type
        role         = profile.role

        # Sécurisation pour les comptes résidence/hôtel déjà créés avec un type incohérent
        professional_profile = getattr(profile, 'professional_profile', None)
        if professional_profile and account_type not in ['hotel', 'residence']:
            account_type = professional_profile.establishment_type or account_type
            profile.account_type = account_type
            profile.role = 'proprietaire'
            profile.save(update_fields=['account_type', 'role'])

    except Exception:
        account_type = 'individu'
        role         = None

    # Les colocataires ne peuvent pas publier
    if account_type == 'individu' and role == 'colocataire':
        from django.contrib import messages
        messages.error(request, _('En tant que colocataire, vous ne pouvez pas publier d\'annonces.'))
        return redirect('logement:home')

    # Sélectionner le bon formulaire et template
    if account_type == 'hotel':
        FormClass = LogementHotelForm
        template  = 'logement/ajouter_logement_hotel.html'
    elif account_type == 'residence':
        FormClass = LogementResidenceForm
        template  = 'logement/ajouter_logement_residence.html'
    elif account_type == 'individu' and role == 'proprietaire':
        FormClass = LogementProprietaireForm
        template  = 'ajouter_logement_proprietaire.html'
    elif account_type == 'individu' and role == 'locataire':
        FormClass = LogementTouristeForm
        template  = 'ajouter_logement_colocation.html'
    else:
        FormClass = LogementProprietaireForm
        template  = 'ajouter_logement_proprietaire.html'

    if request.method == 'POST':
        form    = FormClass(request.POST)
        formset = PhotoLogementFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoLogementFormSet(request.POST, request.FILES, prefix='videos')

        if form.is_valid() and formset.is_valid() and video_formset.is_valid():
            logement              = form.save(commit=False)
            logement.proprietaire = request.user
            logement.account_type = account_type

            if account_type in ['hotel', 'residence']:
                professional_profile = getattr(request.user.profile, 'professional_profile', None)
                establishment_name = (
                    professional_profile.establishment_name
                    if professional_profile and professional_profile.establishment_name
                    else request.user.get_full_name() or request.user.username
                )
                establishment, _ = Etablissement.objects.get_or_create(
                    proprietaire=request.user,
                    defaults={
                        'nom': establishment_name,
                        'type_etablissement': account_type,
                        'ville': logement.ville,
                        'quartier': logement.quartier,
                    },
                )
                logement.etablissement = establishment

            if account_type == 'hotel' and logement.prix_par_nuit:
                logement.prix = logement.prix_par_nuit
            elif account_type == 'residence' and logement.prix_par_mois:
                logement.prix = logement.prix_par_mois

            logement.save()

            # Sauvegarder les photos
            formset.instance = logement
            for form_photo in formset:
                if form_photo.cleaned_data and form_photo.cleaned_data.get('image'):
                    photo          = form_photo.save(commit=False)
                    photo.logement = logement
                    photo.save()

            # Sauvegarder les vidéos
            video_formset.instance = logement
            for form_video in video_formset:
                if form_video.cleaned_data and form_video.cleaned_data.get('video'):
                    video          = form_video.save(commit=False)
                    video.logement = logement
                    video.save()

            return redirect('logement:home')
        else:
            # Erreur : afficher les erreurs
            from django.contrib import messages
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            if not formset.is_valid():
                for form_photo in formset:
                    for field, errors in form_photo.errors.items():
                        for error in errors:
                            messages.error(request, _("Photo - %(field)s: %(error)s") % {
                                'field': field,
                                'error': error,
                            })
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, _("Erreur photos: %(error)s") % {'error': error})
            if not video_formset.is_valid():
                for form_video in video_formset:
                    for field, errors in form_video.errors.items():
                        for error in errors:
                            messages.error(request, _("Vidéo - %(field)s: %(error)s") % {
                                'field': field,
                                'error': error,
                            })
                if video_formset.non_form_errors():
                    for error in video_formset.non_form_errors():
                        messages.error(request, _("Erreur vidéos: %(error)s") % {'error': error})
    else:
        form    = FormClass()
        formset = PhotoLogementFormSet(queryset=PhotoLogement.objects.none(), prefix='photos')
        video_formset = VideoLogementFormSet(queryset=VideoLogement.objects.none(), prefix='videos')

    etablissement = None
    etablissement_categories = []
    if account_type in ['hotel', 'residence']:
        etablissement = Etablissement.objects.filter(proprietaire=request.user).first()
        if etablissement:
            etablissement_categories = etablissement.categories.order_by('type_logement', 'titre')

    return render(request, template, {
        'form':          form,
        'formset':       formset,
        'video_formset': video_formset,
        'account_type':  account_type,
        'etablissement': etablissement,
        'etablissement_categories': etablissement_categories,
    })


# ── MODIFICATION ET SUPPRESSION DES ANNONCES ────────────────────────────────

@login_required
@require_http_methods(["GET", "POST"])
def modifier_logement(request, id):
    """Modifier un logement existant"""
    from django.contrib import messages
    
    logement = get_object_or_404(Logement, id=id)
    
    # Vérifier que l'utilisateur est le propriétaire
    if logement.proprietaire != request.user:
        messages.error(request, _('❌ Vous n\'avez pas la permission de modifier cette annonce.'))
        return redirect('logement:detail_logement', id=logement.id)
    
    account_type = logement.account_type
    
    # Sélectionner le bon formulaire et template
    if account_type == 'hotel':
        FormClass = LogementHotelForm
        template  = 'logement/modifier_logement_hotel.html'
    elif account_type == 'residence':
        FormClass = LogementResidenceForm
        template  = 'logement/modifier_logement_residence.html'
    elif account_type == 'individu':
        FormClass = LogementProprietaireForm
        template  = 'logement/modifier_logement.html'
    else:
        FormClass = LogementProprietaireForm
        template  = 'logement/modifier_logement.html'
    
    if request.method == 'POST':
        form    = FormClass(request.POST, instance=logement)
        formset = PhotoLogementFormSet(request.POST, request.FILES, instance=logement, prefix='photos')
        video_formset = VideoLogementFormSet(request.POST, request.FILES, instance=logement, prefix='videos')
        
        # Valider le formulaire principal et les formsets
        form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        video_formset_valid = video_formset.is_valid()
        
        if form_valid and formset_valid and video_formset_valid:
            logement = form.save(commit=False)
            
            if account_type == 'hotel' and logement.prix_par_nuit:
                logement.prix = logement.prix_par_nuit
            elif account_type == 'residence' and logement.prix_par_mois:
                logement.prix = logement.prix_par_mois
            
            logement.save()
            
            # Sauvegarder les photos
            formset.instance = logement
            formset.save()
            
            # Sauvegarder les vidéos
            video_formset.instance = logement
            video_formset.save()
            
            messages.success(request, _('✅ Annonce mise à jour avec succès!'))
            return redirect('logement:detail_logement', id=logement.id)
        else:
            # Afficher les erreurs du formulaire principal
            if not form_valid:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"❌ {field}: {error}")
            
            # Afficher les erreurs du formset photos
            if not formset_valid:
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, _("❌ Erreur photos: %(error)s") % {'error': error})
                for i, form_photo in enumerate(formset):
                    if form_photo.errors:
                        for field, errors in form_photo.errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, _('❌ Photo %(number)s - %(field)s: %(error)s') % {
                                        'number': i + 1,
                                        'field': field,
                                        'error': error,
                                    })
            
            # Afficher les erreurs du formset vidéos
            if not video_formset_valid:
                if video_formset.non_form_errors():
                    for error in video_formset.non_form_errors():
                        messages.error(request, _("❌ Erreur vidéos: %(error)s") % {'error': error})
                for i, form_video in enumerate(video_formset):
                    if form_video.errors:
                        for field, errors in form_video.errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, _('❌ Vidéo %(number)s - %(field)s: %(error)s') % {
                                        'number': i + 1,
                                        'field': field,
                                        'error': error,
                                    })
    else:
        form    = FormClass(instance=logement)
        formset = PhotoLogementFormSet(instance=logement, prefix='photos')
        video_formset = VideoLogementFormSet(instance=logement, prefix='videos')
    
    return render(request, template, {
        'form':          form,
        'formset':       formset,
        'video_formset': video_formset,
        'logement':      logement,
        'is_editing':    True,
    })


@login_required
@require_http_methods(["POST"])
def supprimer_logement(request, id):
    """Supprimer une annonce"""
    from django.contrib import messages
    
    logement = get_object_or_404(Logement, id=id)
    
    # Vérifier que l'utilisateur est le propriétaire
    if logement.proprietaire != request.user:
        messages.error(request, _('❌ Vous n\'avez pas la permission de supprimer cette annonce.'))
        return redirect('logement:detail_logement', id=logement.id)
    
    titre = logement.titre
    logement.delete()
    
    messages.success(request, _('✅ Annonce "%(title)s" supprimée avec succès.') % {'title': titre})
    return redirect('logement:mes_logements')


# ── DASHBOARDS ────────────────────────────────────────────────────────

@login_required
def mes_logements(request):
    logements = Logement.objects.filter(proprietaire=request.user).prefetch_related('photos')
    return render(request, 'logement/mes_logements.html', {
        'logements': logements,
        'total':     logements.count(),
    })


@login_required
def gestion_logements(request):
    logements = Logement.objects.filter(proprietaire=request.user).prefetch_related('photos')
    return render(request, 'logement/gestion_logements.html', {
        'logements': logements,
        'total':     logements.count(),
    })


@login_required
def mes_reservations(request):
    profile  = request.user.profile
    titre    = 'Réservations — Hôtel' if profile.account_type == 'hotel' else 'Réservations — Résidence'
    template = 'logement/reservations_hotel.html' if profile.account_type == 'hotel' else 'logement/reservations_residence.html'

    reservations = Reservation.objects.filter(
        logement__proprietaire=request.user,
        logement__account_type__in=['hotel', 'residence'],
    ).select_related(
        'logement', 'client_user', 'client_user__profile',
    ).prefetch_related('unites').order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        search_filter = (
            Q(client_nom__icontains=search_query) |
            Q(client_user__first_name__icontains=search_query) |
            Q(client_user__last_name__icontains=search_query) |
            Q(client_user__username__icontains=search_query) |
            Q(client_email__icontains=search_query) |
            Q(client_user__email__icontains=search_query) |
            Q(client_telephone__icontains=search_query) |
            Q(logement__titre__icontains=search_query) |
            Q(unites__numero__icontains=search_query)
        )
        if search_query.isdigit():
            search_filter |= Q(nombre_chambres=int(search_query))
        reservations = reservations.filter(search_filter).distinct()

    selected_status = request.GET.get('statut', '')
    status_values = {value for value, _label in Reservation.STATUT_CHOICES}
    if selected_status in status_values:
        reservations = reservations.filter(statut=selected_status)
    else:
        selected_status = ''

    return render(request, template, {
        'titre':        titre,
        'reservations': reservations,
        'nb_reservations': reservations.count(),
        'search_query': search_query,
        'selected_status': selected_status,
        'status_choices': Reservation.STATUT_CHOICES,
    })


@login_required
def calendrier_reservations(request):
    profile = request.user.profile
    titre   = 'Calendrier — Hôtel' if profile.account_type == 'hotel' else 'Calendrier — Résidence'
    logements = Logement.objects.filter(
        proprietaire=request.user,
        account_type__in=['hotel', 'residence'],
    ).order_by('titre')

    try:
        year = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))
        if month < 1 or month > 12:
            raise ValueError
    except (TypeError, ValueError):
        year, month = date.today().year, date.today().month

    selected_id = request.GET.get('logement')
    logement = logements.filter(id=selected_id).first() if selected_id else logements.first()
    form = BlocageCalendrierForm(
        request.POST or None,
        initial={'logement': logement.id if logement else None},
    )
    form.fields['logement'].queryset = logements

    if request.method == 'POST' and form.is_valid():
        blocage = form.save(commit=False)
        if logements.filter(id=blocage.logement_id).exists():
            blocage.save()
            return redirect(f'{request.path}?year={blocage.date_debut.year}&month={blocage.date_debut.month}&logement={blocage.logement_id}')

    days = []
    if logement:
        month_days = calendar_module.Calendar(firstweekday=0).monthdayscalendar(year, month)
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar_module.monthrange(year, month)[1]) + timedelta(days=1)
        reservations = logement.reservations.filter(
            date_arrivee__lt=month_end,
            date_depart__gt=month_start,
            statut__in=['pending', 'confirmed'],
        ).select_related('client_user').prefetch_related('unites').order_by('date_arrivee')
        blocks = logement.blocages.filter(
            date_debut__lt=month_end,
            date_fin__gt=month_start,
        )
        overrides = {item.date: item for item in logement.disponibilites.filter(date__year=year, date__month=month)}

        day_reservations_by_date = {}
        for reservation in reservations:
            current = reservation.date_arrivee
            while current < reservation.date_depart and current < month_end:
                if current >= month_start:
                    day_reservations_by_date.setdefault(current, []).append(reservation)
                current += timedelta(days=1)

        block_by_date = {}
        for block in blocks:
            current = block.date_debut
            while current < block.date_fin and current < month_end:
                if current >= month_start:
                    block_by_date[current] = block
                current += timedelta(days=1)

        for week in month_days:
            for day_number in week:
                if not day_number:
                    days.append(None)
                    continue
                current = date(year, month, day_number)
                block = block_by_date.get(current)
                day_reservations = day_reservations_by_date.get(current, [])
                reserved_units = sum(
                    len(item.unites.all()) or item.nombre_chambres or 1
                    for item in day_reservations
                )
                available_units = max(logement.unites_totales - reserved_units, 0)
                override = overrides.get(current)
                confirmed_reservations = [
                    item for item in day_reservations if item.statut == 'confirmed'
                ]
                pending_reservations = [
                    item for item in day_reservations if item.statut == 'pending'
                ]
                if block or (override and override.statut == 'bloquer'):
                    status = 'blocked'
                    label = block.motif if block else 'Indisponible'
                elif confirmed_reservations:
                    status, label = 'reserved', 'Réservé'
                elif pending_reservations:
                    status, label = 'pending', 'En attente'
                elif override and override.statut == 'occupe':
                    status, label = 'reserved', 'Occupé'
                else:
                    status, label = 'available', 'Disponible'
                days.append({
                    'number': day_number,
                    'status': status,
                    'label': label,
                    'reserved_units': reserved_units,
                    'available_units': available_units,
                    'reservations': day_reservations,
                    'is_blocked': bool(block or (override and override.statut == 'bloquer')),
                })

    previous = (date(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_month = (date(year, month, 28) + timedelta(days=4)).replace(day=1)
    return render(request, 'logement/calendrier_reservations.html', {
        'titre': titre,
        'logements': logements,
        'logement': logement,
        'blocage_form': form,
        'days': days,
        'calendar_month': date(year, month, 1),
        'previous_month': previous,
        'next_month': next_month,
        'weekdays': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        'inventory_total': logement.unites_totales if logement else 0,
        'inventory_reserved': logement.reserved_units_for_date(date.today()) if logement else 0,
        'inventory_available': logement.available_units_for_date(date.today()) if logement else 0,
    })


@login_required
def mes_paiements(request):
    paiements = (
        Paiement.objects.filter(reservation__logement__proprietaire=request.user)
        .select_related('reservation', 'reservation__logement', 'reservation__client_user')
        .order_by('-created_at')
    )

    total_recu = sum((p.montant for p in paiements if p.statut == 'completed'), 0)
    total_en_attente = sum((p.montant for p in paiements if p.statut == 'pending'), 0)

    return render(request, 'logement/mes_paiements.html', {
        'paiements': paiements,
        'total_recu': total_recu,
        'total_en_attente': total_en_attente,
        'nb_paiements': paiements.count(),
    })


@login_required
def mes_clients(request):
    profile = request.user.profile
    titre   = 'Clients — Hôtel' if profile.account_type == 'hotel' else 'Locataires — Résidence'
    reservations = Reservation.objects.filter(
        logement__proprietaire=request.user,
        logement__account_type__in=['hotel', 'residence'],
    ).select_related('logement', 'client_user').order_by('-created_at')

    clients = {}
    for reservation in reservations:
        key = reservation.client_user_id or reservation.client_email
        if key not in clients:
            clients[key] = {
                'client_name': reservation.client_user.get_full_name() or reservation.client_user.username if reservation.client_user else reservation.client_nom,
                'email': reservation.client_email,
                'telephone': reservation.client_telephone,
                'derniere_reservation': reservation.date_depart,
                'total_depense': 0,
                'nb_reservations': 0,
                'logements': [],
            }

        client = clients[key]
        client['total_depense'] += reservation.montant_final
        client['nb_reservations'] += 1
        client['logements'].append(reservation.logement.titre)
        if reservation.date_depart > client['derniere_reservation']:
            client['derniere_reservation'] = reservation.date_depart

    client_list = sorted(clients.values(), key=lambda item: item['total_depense'], reverse=True)

    return render(request, 'logement/mes_clients.html', {
        'titre':   titre,
        'clients': client_list,
        'nb_clients': len(client_list),
    })


@login_required
def avis_clients(request):
    avis = AvisLogement.objects.filter(
        logement__proprietaire=request.user,
    ).select_related('logement', 'reservation', 'auteur').order_by('-created_at')

    note_moyenne = 0
    if avis.exists():
        notes = [item.note_logement for item in avis if item.note_logement is not None]
        if notes:
            note_moyenne = round(sum(notes) / len(notes), 1)

    return render(request, 'logement/avis_clients.html', {
        'avis': avis,
        'note_moyenne': note_moyenne,
        'nb_avis': avis.count(),
    })


@login_required
def statistiques_professionnel(request):
    logements = Logement.objects.filter(proprietaire=request.user, account_type__in=['hotel', 'residence'])
    reservations = Reservation.objects.filter(logement__proprietaire=request.user).select_related('logement')
    avis = AvisLogement.objects.filter(logement__proprietaire=request.user)

    total_logements = logements.count()
    total_reservations = reservations.count()
    revenu_total = sum((reservation.montant_final for reservation in reservations if reservation.statut in ['confirmed', 'completed']), 0)

    note_moyenne = 0
    notes = [item.note_logement for item in avis if item.note_logement is not None]
    if notes:
        note_moyenne = round(sum(notes) / len(notes), 1)

    occupied_nights = sum((reservation.nombre_nuits or 0 for reservation in reservations if reservation.statut in ['confirmed', 'completed']))
    available_nights = max(total_logements * 30, 1)
    taux_occupation = round((occupied_nights / available_nights) * 100, 1) if available_nights else 0

    # Build a stable twelve-month series so the dashboard remains useful even
    # when the database contains sparse or incomplete historical data.
    today = date.today()
    months = []
    for offset in range(11, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        month_year, month_number = divmod(month_index, 12)
        month_number += 1
        month_start = date(month_year, month_number, 1)
        if month_number == 12:
            month_end = date(month_year + 1, 1, 1)
        else:
            month_end = date(month_year, month_number + 1, 1)
        months.append((month_start, month_end))

    month_labels = [month_start.strftime('%b %Y') for month_start, _ in months]
    monthly_revenue = []
    monthly_reservations = []
    monthly_occupancy = []
    monthly_reviews = []

    for month_start, month_end in months:
        month_reservations = [
            reservation for reservation in reservations
            if month_start <= reservation.date_arrivee < month_end
        ]
        completed_month_reservations = [
            reservation for reservation in month_reservations
            if reservation.statut in ['confirmed', 'completed']
        ]
        month_nights = sum(
            (reservation.nombre_nuits or 0) for reservation in completed_month_reservations
        )
        days_in_month = (month_end - month_start).days
        capacity = max(sum(logement.unites_totales for logement in logements) * days_in_month, 1)
        month_reviews = [
            review for review in avis
            if month_start <= review.created_at.date() < month_end
            and review.note_logement is not None
        ]

        monthly_revenue.append(float(sum(
            reservation.montant_final for reservation in completed_month_reservations
        )))
        monthly_reservations.append(len(month_reservations))
        monthly_occupancy.append(round(min((month_nights / capacity) * 100, 100), 1))
        monthly_reviews.append(round(
            sum(review.note_logement for review in month_reviews) / len(month_reviews), 1
        ) if month_reviews else 0)

    reservation_statuses = [
        {'label': label, 'value': reservations.filter(statut=value).count()}
        for value, label in Reservation.STATUT_CHOICES
    ]
    property_revenue = []
    for logement in logements:
        amount = sum(
            reservation.montant_final for reservation in reservations
            if reservation.logement_id == logement.id
            and reservation.statut in ['confirmed', 'completed']
        )
        property_revenue.append({'label': logement.titre, 'value': float(amount)})

    return render(request, 'logement/statistiques.html', {
        'total_logements': total_logements,
        'total_reservations': total_reservations,
        'taux_occupation': taux_occupation,
        'revenu_total': revenu_total,
        'note_moyenne': note_moyenne,
        'nb_avis': avis.count(),
        'reservations': reservations.order_by('-created_at')[:10],
        'chart_data': {
            'labels': month_labels,
            'revenus': monthly_revenue,
            'reservations': monthly_reservations,
            'occupation': monthly_occupancy,
            'avis': monthly_reviews,
            'statuts': reservation_statuses,
            'logements': property_revenue,
        },
    })