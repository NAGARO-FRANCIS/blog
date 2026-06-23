from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import (
    LogementProprietaireForm, LogementColocataireForm, LogementHotelForm, LogementResidenceForm,
    RechercheLogementForm, PhotoLogementFormSet, VideoLogementFormSet
)
from .models import Logement, PhotoLogement, VideoLogement


@login_required
def choisir_type_annonce(request):
    """Affiche la page de sélection du type d'annonce"""
    return render(request, 'logement/choisir_type_annonce.html')


def home(request):
    """Page d'accueil avec annonces filtrées selon le rôle"""
    form = RechercheLogementForm(request.GET or None)

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

        elif role == 'colocataire':
            # Colocataire → voit hôtels, résidences, propriétaires ET locataires
            logements = Logement.objects.filter(
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role__in=['proprietaire', 'locataire']))
            )

        elif role == 'locataire':
            # Locataire → voit hôtels, résidences, propriétaires individuels
            logements = Logement.objects.filter(
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            )

        elif role == 'proprietaire':
            # Propriétaire → voit hôtels, résidences ET autres propriétaires individuels
            logements = Logement.objects.filter(
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            )

        else:
            logements = Logement.objects.all()

    else:
        # Non connecté → voit tout
        logements = Logement.objects.all()

    # ── FILTRES DE RECHERCHE (inchangés) ─────────────────────────────
    if form.is_valid():
        q             = form.cleaned_data.get('q')
        ville         = form.cleaned_data.get('ville')
        prix_max      = form.cleaned_data.get('prix_max')
        type_logement = form.cleaned_data.get('type_logement')

        if q:
            logements = logements.filter(
                Q(titre__icontains=q) | Q(description__icontains=q)
            )
        if ville:
            logements = logements.filter(ville__icontains=ville)
        if prix_max:
            logements_filtered = []
            for logement in logements:
                prix = logement.prix_par_nuit or logement.prix_par_mois or logement.prix
                if prix and prix <= prix_max:
                    logements_filtered.append(logement)
            logements = logements_filtered
        if type_logement:
            logements = logements.filter(type_logement=type_logement)

    logements = logements.prefetch_related('photos').order_by('-created_at')

    context = {
        'form':      form,
        'logements': logements,
        'annonces':  logements,  # Pour compatibilité avec le template
        'user_type': request.user.profile.account_type if request.user.is_authenticated else 'anonymous',
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
        q             = form.cleaned_data.get('q')
        ville         = form.cleaned_data.get('ville')
        prix_max      = form.cleaned_data.get('prix_max')
        type_logement = form.cleaned_data.get('type_logement')

        if q:
            hotels      = hotels.filter(Q(titre__icontains=q) | Q(description__icontains=q))
            residences  = residences.filter(Q(titre__icontains=q) | Q(description__icontains=q))
            individuals = individuals.filter(Q(titre__icontains=q) | Q(description__icontains=q))
        if ville:
            hotels      = hotels.filter(ville__icontains=ville)
            residences  = residences.filter(ville__icontains=ville)
            individuals = individuals.filter(ville__icontains=ville)
        if type_logement:
            hotels      = hotels.filter(type_logement=type_logement)
            residences  = residences.filter(type_logement=type_logement)
            individuals = individuals.filter(type_logement=type_logement)
        if prix_max:
            hotels_filtered      = [h for h in hotels      if h.prix_par_nuit  and h.prix_par_nuit  <= prix_max]
            residences_filtered  = [r for r in residences  if r.prix_par_mois  and r.prix_par_mois  <= prix_max]
            individuals_filtered = [i for i in individuals if (i.prix or 0)    and i.prix           <= prix_max]
            hotels      = hotels_filtered
            residences  = residences_filtered
            individuals = individuals_filtered

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


@require_http_methods(["GET", "POST"])
def reserver_logement(request, id):
    """Créer une réservation (pour hôtels et résidences)"""
    from django.contrib import messages
    
    logement = get_object_or_404(Logement, id=id)

    if logement.account_type not in ['hotel', 'residence']:
        messages.error(
            request, 
            '❌ Les annonces particulières ne sont pas réservables en ligne. '
            'Veuillez contacter directement le propriétaire.'
        )
        return redirect('logement:detail_logement', id=logement.id)

    if request.method == 'POST':
        from .forms import ReservationForm
        form = ReservationForm(request.POST, logement=logement)

        if form.is_valid():
            reservation          = form.save(commit=False)
            reservation.logement = logement
            
            # Remplir les champs de pricing depuis le logement
            reservation.prix_par_nuit = logement.prix_par_nuit or 0
            if logement.frais_nettoyage:
                reservation.frais_nettoyage_reservation = logement.frais_nettoyage
            
            if request.user.is_authenticated:
                reservation.client_user  = request.user
                reservation.client_nom   = request.user.get_full_name() or request.user.username
                reservation.client_email = request.user.email
            reservation.save()
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
    import stripe
    import os
    import json
    from django.http import JsonResponse
    from django.contrib import messages

    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.user.is_authenticated and reservation.client_user != request.user:
        if request.user != reservation.logement.proprietaire:
            return redirect('logement:home')

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

    # Traitement POST (traitement du paiement)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'stripe')
        
        # Créer ou mettre à jour le paiement
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
        
        # Traiter selon la méthode
        try:
            if payment_method == 'mouv':
                # MOUV - Mobile Money
                mouv_number = request.POST.get('mouv_number', '')
                if not mouv_number:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez entrer votre numéro MOUV'
                    })
                
                paiement.statut = 'pending'
                paiement.description = f"MOUV: {mouv_number}"
                paiement.save()
                
                messages.success(request, f'✅ Paiement MOUV en cours de traitement. Veuillez confirmer sur votre téléphone.')
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
                
                messages.success(request, '✅ Paiement Orange Money en cours de traitement.')
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
                
                messages.success(request, '✅ Paiement Wave en cours de traitement.')
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
                messages.info(request, '💳 Paiement par carte bancaire en cours...')
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
                messages.info(request, '🏦 Nos coordonnées bancaires ont été envoyées par email.')
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
                
                messages.success(request, '✅ Réservation confirmée. Paiement à l\'arrivée.')
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
    
    # Vérifier les permissions
    if request.user.is_authenticated and reservation.client_user != request.user:
        if request.user != reservation.logement.proprietaire:
            return redirect('logement:home')
    
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
    except Exception:
        account_type = 'individu'
        role         = None

    # Les colocataires ne peuvent pas publier
    if account_type == 'individu' and role == 'colocataire':
        from django.contrib import messages
        messages.error(request, 'En tant que colocataire, vous ne pouvez pas publier d\'annonces.')
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
        FormClass = LogementColocataireForm
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
                            messages.error(request, f"Photo - {field}: {error}")
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, f"Erreur photos: {error}")
            if not video_formset.is_valid():
                for form_video in video_formset:
                    for field, errors in form_video.errors.items():
                        for error in errors:
                            messages.error(request, f"Vidéo - {field}: {error}")
                if video_formset.non_form_errors():
                    for error in video_formset.non_form_errors():
                        messages.error(request, f"Erreur vidéos: {error}")
    else:
        form    = FormClass()
        formset = PhotoLogementFormSet(queryset=PhotoLogement.objects.none(), prefix='photos')
        video_formset = VideoLogementFormSet(queryset=VideoLogement.objects.none(), prefix='videos')

    return render(request, template, {
        'form':          form,
        'formset':       formset,
        'video_formset': video_formset,
        'account_type':  account_type,
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
        messages.error(request, '❌ Vous n\'avez pas la permission de modifier cette annonce.')
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
            
            messages.success(request, '✅ Annonce mise à jour avec succès!')
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
                        messages.error(request, f"❌ Erreur photos: {error}")
                for i, form_photo in enumerate(formset):
                    if form_photo.errors:
                        for field, errors in form_photo.errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f"❌ Photo {i+1} - {field}: {error}")
            
            # Afficher les erreurs du formset vidéos
            if not video_formset_valid:
                if video_formset.non_form_errors():
                    for error in video_formset.non_form_errors():
                        messages.error(request, f"❌ Erreur vidéos: {error}")
                for i, form_video in enumerate(video_formset):
                    if form_video.errors:
                        for field, errors in form_video.errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f"❌ Vidéo {i+1} - {field}: {error}")
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
        messages.error(request, '❌ Vous n\'avez pas la permission de supprimer cette annonce.')
        return redirect('logement:detail_logement', id=logement.id)
    
    titre = logement.titre
    logement.delete()
    
    messages.success(request, f'✅ Annonce "{titre}" supprimée avec succès.')
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

    return render(request, template, {
        'titre':        titre,
        'reservations': [],
    })


@login_required
def calendrier_reservations(request):
    profile = request.user.profile
    titre   = 'Calendrier — Hôtel' if profile.account_type == 'hotel' else 'Calendrier — Résidence'
    return render(request, 'logement/calendrier_reservations.html', {'titre': titre})


@login_required
def mes_paiements(request):
    return render(request, 'logement/mes_paiements.html', {'paiements': []})


@login_required
def mes_clients(request):
    profile = request.user.profile
    titre   = 'Clients — Hôtel' if profile.account_type == 'hotel' else 'Locataires — Résidence'
    return render(request, 'logement/mes_clients.html', {
        'titre':   titre,
        'clients': [],
    })


@login_required
def avis_clients(request):
    return render(request, 'logement/avis_clients.html', {'avis': []})


@login_required
def statistiques_professionnel(request):
    return render(request, 'logement/statistiques.html', {
        'total_logements': 0,
        'taux_occupation': 0,
        'revenu_total':    0,
        'note_moyenne':    0,
    })