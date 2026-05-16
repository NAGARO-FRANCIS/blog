from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .forms import (
    LogementForm, LogementHotelForm, LogementResidenceForm,
    RechercheLogementForm, PhotoLogementFormSet
)
from .models import Logement, PhotoLogement


def home(request):
    """Page d'accueil avec annonces filtrées selon le type de compte"""
    form = RechercheLogementForm(request.GET or None)
    
    # Déterminer quel type de logements afficher
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            account_type = profile.account_type
            
            if account_type == 'hotel':
                # Hôtel voit les autres hôtels
                logements = Logement.objects.filter(account_type='hotel')
            elif account_type == 'residence':
                # Résidence voit les autres résidences
                logements = Logement.objects.filter(account_type='residence')
            else:
                # Locataires/Colocataires voient location individuelle + colocation
                logements = Logement.objects.filter(
                    account_type__in=['individu']  # À adapter quand colocation app sera prête
                )
        except:
            # Utilisateur sans profil: afficher location individuelle
            logements = Logement.objects.filter(account_type='individu')
    else:
        # Touriste anonyme: voit HÔTELS + RÉSIDENCES
        logements = Logement.objects.filter(
            account_type__in=['hotel', 'residence']
        )
    
    # Appliquer les filtres de recherche
    if form.is_valid():
        q = form.cleaned_data.get('q')
        ville = form.cleaned_data.get('ville')
        prix_max = form.cleaned_data.get('prix_max')
        type_logement = form.cleaned_data.get('type_logement')
        
        if q:
            logements = logements.filter(
                Q(titre__icontains=q) | Q(description__icontains=q)
            )
        if ville:
            logements = logements.filter(ville__icontains=ville)
        if prix_max:
            # Chercher le prix approprié selon le type
            logements_filtered = []
            for logement in logements:
                prix = logement.prix_par_nuit or logement.prix_par_mois or logement.prix
                if prix and prix <= prix_max:
                    logements_filtered.append(logement)
            logements = logements_filtered
        if type_logement:
            logements = logements.filter(type_logement=type_logement)
    
    # Pré-charger les relations
    logements = logements.prefetch_related('photos').order_by('-created_at')

    context = {
        'form': form,
        'logements': logements,
        'user_type': request.user.profile.account_type if request.user.is_authenticated else 'anonymous',
    }
    
    return render(request, 'acceuil.html', context)


@require_http_methods(["GET"])
def listings_all_types(request):
    """Page professionnelle affichant tous les types de propriétés distincts"""
    
    # Récupérer les trois types séparément
    hotels = Logement.objects.filter(account_type='hotel').prefetch_related('photos').order_by('-created_at')
    residences = Logement.objects.filter(account_type='residence').prefetch_related('photos').order_by('-created_at')
    individuals = Logement.objects.filter(account_type='individu').prefetch_related('photos').order_by('-created_at')
    
    # Appliquer les filtres de recherche si fournis
    form = RechercheLogementForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        ville = form.cleaned_data.get('ville')
        prix_max = form.cleaned_data.get('prix_max')
        type_logement = form.cleaned_data.get('type_logement')
        
        # Filtre par recherche textuelle
        if q:
            hotels = hotels.filter(Q(titre__icontains=q) | Q(description__icontains=q))
            residences = residences.filter(Q(titre__icontains=q) | Q(description__icontains=q))
            individuals = individuals.filter(Q(titre__icontains=q) | Q(description__icontains=q))
        
        # Filtre par ville
        if ville:
            hotels = hotels.filter(ville__icontains=ville)
            residences = residences.filter(ville__icontains=ville)
            individuals = individuals.filter(ville__icontains=ville)
        
        # Filtre par type de logement
        if type_logement:
            hotels = hotels.filter(type_logement=type_logement)
            residences = residences.filter(type_logement=type_logement)
            individuals = individuals.filter(type_logement=type_logement)
        
        # Filtre par prix max (adapté à chaque type)
        if prix_max:
            hotels_filtered = []
            residences_filtered = []
            individuals_filtered = []
            
            for h in hotels:
                if h.prix_par_nuit and h.prix_par_nuit <= prix_max:
                    hotels_filtered.append(h)
            
            for r in residences:
                if r.prix_par_mois and r.prix_par_mois <= prix_max:
                    residences_filtered.append(r)
            
            for i in individuals:
                prix = i.prix or 0
                if prix and prix <= prix_max:
                    individuals_filtered.append(i)
            
            hotels = hotels_filtered
            residences = residences_filtered
            individuals = individuals_filtered
    
    context = {
        'form': form,
        'hotels': hotels,
        'residences': residences,
        'individuals': individuals,
        'hotel_count': len(hotels) if isinstance(hotels, list) else hotels.count(),
        'residence_count': len(residences) if isinstance(residences, list) else residences.count(),
        'individu_count': len(individuals) if isinstance(individuals, list) else individuals.count(),
        'total_count': (len(hotels) if isinstance(hotels, list) else hotels.count()) + 
                       (len(residences) if isinstance(residences, list) else residences.count()) + 
                       (len(individuals) if isinstance(individuals, list) else individuals.count()),
    }
    
    return render(request, 'logement/listings_all_types.html', context)


@require_http_methods(["GET"])
def detail_logement(request, id):
    """Page de détail d'un logement avec formulaire de réservation"""
    logement = get_object_or_404(Logement, id=id)
    
    # Vérifier les permissions de visibilité
    if request.user.is_authenticated:
        user_type = request.user.profile.account_type
        # Permettre la vue si c'est public ou si c'est le propriétaire
        if logement.account_type not in ['hotel', 'residence'] and user_type not in ['hotel', 'residence']:
            # Locataire peut voir location individuelle
            pass
        elif logement.account_type == 'hotel' and user_type != 'hotel':
            # Hôtels visibles pour les touristes/anonymes
            pass
        elif logement.account_type == 'residence' and user_type not in ['residence']:
            # Résidences visibles pour les touristes/anonymes
            pass
    
    photos = logement.photos.all()
    reservations_count = logement.reservations.filter(statut='confirmed').count()
    
    context = {
        'logement': logement,
        'photos': photos,
        'reservations_count': reservations_count,
    }
    
    return render(request, 'logement/detail_logement.html', context)


@require_http_methods(["GET", "POST"])
def reserver_logement(request, id):
    """Créer une réservation (pour hôtels et résidences)"""
    logement = get_object_or_404(Logement, id=id)
    
    # Vérifier que c'est un hôtel ou résidence
    if logement.account_type not in ['hotel', 'residence']:
        return redirect('logement:home')
    
    if request.method == 'POST':
        from .forms import ReservationForm
        form = ReservationForm(request.POST, logement=logement)
        
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.logement = logement
            
            # Si utilisateur connecté
            if request.user.is_authenticated:
                reservation.client_user = request.user
                reservation.client_nom = request.user.get_full_name() or request.user.username
                reservation.client_email = request.user.email
            
            reservation.save()
            
            # Rediriger vers le paiement
            return redirect('logement:paiement', reservation_id=reservation.id)
    else:
        from .forms import ReservationForm
        form = ReservationForm(logement=logement)
    
    context = {
        'logement': logement,
        'form': form,
    }
    
    return render(request, 'logement/reserver_logement.html', context)


@require_http_methods(["GET"])
def paiement_reservation(request, reservation_id):
    """Page de paiement Stripe pour la réservation"""
    from .models import Reservation
    import stripe
    import os
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Vérifier les permissions
    if request.user.is_authenticated and reservation.client_user != request.user:
        if request.user != reservation.logement.proprietaire:
            return redirect('logement:home')
    
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
    
    context = {
        'reservation': reservation,
        'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY', ''),
    }
    
    return render(request, 'logement/paiement_reservation.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def ajouter_logement(request):
    """Ajouter un logement avec formulaire différencié selon le type de compte"""
    
    # Vérifier les permissions : seuls propriétaires et locataires peuvent publier
    try:
        profile = request.user.profile
        account_type = profile.account_type
        role = profile.role
        
        # Vérifier si l'utilisateur peut publier
        if account_type == 'individu' and role == 'colocataire':
            # Les colocataires ne peuvent pas publier d'annonces
            from django.contrib import messages
            messages.error(request, '❌ En tant que colocataire, vous ne pouvez pas publier d\'annonces. Vous pouvez uniquement consulter les annonces existantes.')
            return redirect('logement:home')
    except:
        account_type = 'individu'
        role = None
    
    # Déterminer le type de compte
    try:
        profile = request.user.profile
        account_type = profile.account_type
    except:
        account_type = 'individu'
    
    # Sélectionner le bon formulaire selon le type de compte
    if account_type == 'hotel':
        FormClass = LogementHotelForm
        template = 'logement/ajouter_logement_hotel.html'
    elif account_type == 'residence':
        FormClass = LogementResidenceForm
        template = 'logement/ajouter_logement_residence.html'
    else:
        FormClass = LogementForm
        template = 'ajouter_logement.html'
    
    if request.method == 'POST':
        form = FormClass(request.POST)
        formset = PhotoLogementFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            logement = form.save(commit=False)
            logement.proprietaire = request.user
            logement.account_type = account_type
            
            # Remplir le champ prix intelligemment selon le type de compte
            if account_type == 'hotel' and logement.prix_par_nuit:
                logement.prix = logement.prix_par_nuit
            elif account_type == 'residence' and logement.prix_par_mois:
                logement.prix = logement.prix_par_mois
            # Pour individu, prix est déjà dans le formulaire
            
            logement.save()
            
            # Sauvegarder les photos - only save non-empty forms
            formset.instance = logement
            for form_photo in formset:
                if form_photo.cleaned_data and form_photo.cleaned_data.get('image'):
                    photo = form_photo.save(commit=False)
                    photo.logement = logement
                    photo.save()
            
            print(f"✅ Logement créé: {logement.titre} (Type: {logement.account_type})")
            return redirect('home')
        else:
            print("❌ Erreurs du formulaire:")
            print(f"Form errors: {form.errors}")
            print(f"Formset errors: {formset.errors}")
    else:
        form = FormClass()
        formset = PhotoLogementFormSet(queryset=PhotoLogement.objects.none())

    return render(request, template, {
        'form': form,
        'formset': formset,
        'account_type': account_type,
    })



# ================================
# NOUVELLES VUES POUR DASHBOARDS
# ================================

@login_required
def mes_logements(request):
    """Liste de tous les logements du propriétaire"""
    logements = Logement.objects.filter(proprietaire=request.user).prefetch_related('photos')
    
    context = {
        'logements': logements,
        'total': logements.count(),
    }
    return render(request, 'logement/mes_logements.html', context)


@login_required
def gestion_logements(request):
    """Gestion avancée des logements"""
    logements = Logement.objects.filter(proprietaire=request.user).prefetch_related('photos')
    
    context = {
        'logements': logements,
        'total': logements.count(),
    }
    return render(request, 'logement/gestion_logements.html', context)


@login_required
def mes_reservations(request):
    """Liste des réservations pour les logements de l'utilisateur"""
    profile = request.user.profile
    
    # Afficher différent contenu selon le type de compte
    if profile.account_type == 'hotel':
        titre = 'Réservations - Hôtel'
        template = 'logement/reservations_hotel.html'
    else:
        titre = 'Réservations - Résidence'
        template = 'logement/reservations_residence.html'
    
    context = {
        'titre': titre,
        'reservations': [],  # À adapter avec modèle réel
    }
    return render(request, template, context)


@login_required
def calendrier_reservations(request):
    """Calendrier interactif des réservations"""
    profile = request.user.profile
    
    if profile.account_type == 'hotel':
        titre = 'Calendrier - Hôtel'
    else:
        titre = 'Calendrier - Résidence'
    
    context = {
        'titre': titre,
    }
    return render(request, 'logement/calendrier_reservations.html', context)


@login_required
def mes_paiements(request):
    """Gestion des paiements et facturation"""
    context = {
        'paiements': [],  # À adapter avec modèle réel
    }
    return render(request, 'logement/mes_paiements.html', context)


@login_required
def mes_clients(request):
    """Liste des clients et locataires"""
    profile = request.user.profile
    
    if profile.account_type == 'hotel':
        titre = 'Clients - Hôtel'
    else:
        titre = 'Locataires - Résidence'
    
    context = {
        'titre': titre,
        'clients': [],  # À adapter avec modèle réel
    }
    return render(request, 'logement/mes_clients.html', context)


@login_required
def avis_clients(request):
    """Consultation des avis et évaluations"""
    context = {
        'avis': [],  # À adapter avec modèle réel
    }
    return render(request, 'logement/avis_clients.html', context)


@login_required
def statistiques_professionnel(request):
    """Tableau de bord statistiques pour professionnels"""
    profile = request.user.profile
    
    # Données statistiques
    context = {
        'total_logements': 0,
        'taux_occupation': 0,
        'revenu_total': 0,
        'note_moyenne': 0,
    }
    return render(request, 'logement/statistiques.html', context)
