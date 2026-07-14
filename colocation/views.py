from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .forms import ColocationAnnonceForm, RechercheAnnonceForm, PhotoColocationFormSet
from .models import ColocationAnnonce, Favori
from logement.models import Logement, FavoriLogement
from logement.forms import RechercheLogementForm
from django.shortcuts import render

def home(request):
    annonces = Logement.objects.all()[:5]
    
    # Récupérer les IDs des favoris si l'utilisateur est connecté
    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(FavoriLogement.objects.filter(utilisateur=request.user).values_list('logement_id', flat=True))
    
    return render(request, 'acceuil.html', {'annonces': annonces, 'favoris_ids': favoris_ids})

def liste_annonces(request):
    form = RechercheLogementForm(request.GET or None)

    user = request.user
    if not user.is_authenticated:
        annonces = Logement.objects.prefetch_related('photos').order_by('-created_at')
    else:
        try:
            role         = user.profile.role
            account_type = user.profile.account_type
        except Exception:
            role         = None
            account_type = None

        if account_type in ['hotel', 'residence']:
            annonces = Logement.objects.prefetch_related('photos').order_by('-created_at')
        elif role == 'touriste':
            annonces = Logement.objects.filter(
                Q(proprietaire=user) |
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role__in=['proprietaire', 'locataire']))
            ).prefetch_related('photos').order_by('-created_at')
        elif role == 'locataire':
            annonces = Logement.objects.filter(
                Q(proprietaire=user) |
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            ).prefetch_related('photos').order_by('-created_at')
        elif role == 'proprietaire':
            annonces = Logement.objects.filter(
                Q(account_type__in=['hotel', 'residence']) |
                (Q(account_type='individu') & 
                 Q(proprietaire__isnull=False) & 
                 Q(proprietaire__profile__role='proprietaire'))
            ).prefetch_related('photos').order_by('-created_at')
        else:
            annonces = Logement.objects.prefetch_related('photos').order_by('-created_at')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        ville = form.cleaned_data.get('ville')
        prix_max = form.cleaned_data.get('prix_max')
        type_logement = form.cleaned_data.get('type_logement')

        if q:
            annonces = annonces.filter(
                Q(titre__icontains=q) | Q(description__icontains=q)
            )
        if ville:
            annonces = annonces.filter(ville__icontains=ville)
        if prix_max:
            annonces_filtered = []
            for logement in annonces:
                prix = logement.prix_par_nuit or logement.prix_par_mois or logement.prix
                if prix and prix <= prix_max:
                    annonces_filtered.append(logement)
            annonces = annonces_filtered
        if type_logement:
            annonces = annonces.filter(type_logement=type_logement)

    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(FavoriLogement.objects.filter(utilisateur=request.user).values_list('logement_id', flat=True))

    return render(
        request,
        'colocation/liste_annonces.html',
        {'form': form, 'annonces': annonces, 'favoris_ids': favoris_ids},
    )


def detail_annonce(request, annonce_id):
    """Affiche les détails complets d'une annonce"""
    annonce = get_object_or_404(
        ColocationAnnonce.objects.prefetch_related('photos'),
        pk=annonce_id
    )
    
    # Vérifier si l'annonce est dans les favoris de l'utilisateur
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favori.objects.filter(
            utilisateur=request.user,
            annonce=annonce
        ).exists()
    
    return render(request, 'colocation/detail_annonce.html', {
        'annonce': annonce,
        'is_favorite': is_favorite,
    })


@login_required
@require_http_methods(["GET", "POST"])
def publier_annonce(request):
    """Publier une annonce de colocation - réservé aux touristes et propriétaires individuels"""
    try:
        profile = request.user.profile
        account_type = profile.account_type
        role = profile.role
    except:
        return render(request, 'colocation/publier_annonce.html', {
            'form': None,
            'error': 'Votre profil doit être complété avant de publier une annonce.'
        })
    
    # Rediriger les résidences et hôtels vers leur formulaire spécifique
    if account_type in ['residence', 'hotel']:
        from django.contrib import messages
        messages.info(request, 'Vous avez accès au formulaire de publication pour votre type d\'établissement.')
        return redirect('logement:ajouter_logement')
    
    # Les touristes seuls peuvent publier des annonces de colocation
    if account_type == 'individu' and role not in ['touriste', 'proprietaire', 'locataire']:
        return render(request, 'colocation/publier_annonce.html', {
            'form': None,
            'error': 'Vous devez avoir un rôle valide pour publier une annonce.'
        })

    if request.method == 'POST':
        form = ColocationAnnonceForm(request.POST)
        formset = PhotoColocationFormSet(request.POST, request.FILES, prefix='photos')
        
        if form.is_valid():
            # Valider le formset avec gestion personnalisée
            formset_valid = formset.is_valid()
            
            if formset_valid:
                try:
                    # Sauvegarder l'annonce
                    annonce = form.save(commit=False)
                    annonce.proprietaire = request.user
                    annonce.save()
                    
                    # Sauvegarder les photos
                    formset.instance = annonce
                    formset.save()
                    
                    return redirect('colocation:colocation_home')
                except Exception as error:
                    form.add_error(None, f"Erreur lors de la sauvegarde: {str(error)}")
            else:
                # Afficher les erreurs du formset
                for error in formset.non_form_errors():
                    form.add_error(None, str(error))
                # Afficher les erreurs individuelles des formulaires du formset
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, error_list in form_errors.items():
                            if error_list:
                                form.add_error(None, f"Photo {i+1} - {field}: {error_list[0]}")
        
        # Retourner le formulaire avec les erreurs
        return render(request, 'colocation/publier_annonce.html', {
            'form': form,
            'formset': formset,
        })
    else:
        form = ColocationAnnonceForm()
        formset = PhotoColocationFormSet(prefix='photos')

    return render(request, 'colocation/publier_annonce.html', {
        'form': form,
        'formset': formset,
    })


@login_required
@require_http_methods(["POST"])
def toggle_favori(request, annonce_id):
    annonce = get_object_or_404(ColocationAnnonce, pk=annonce_id)
    favori, created = Favori.objects.get_or_create(
        utilisateur=request.user,
        annonce=annonce,
    )
    if not created:
        favori.delete()
        is_favorite = False
    else:
        is_favorite = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_favorite})
    return redirect('colocation:colocation_home')


@login_required
def mes_favoris(request):
    favoris = Favori.objects.filter(utilisateur=request.user).select_related('annonce').prefetch_related('annonce__photos')
    return render(request, 'colocation/mes_favoris.html', {'favoris': favoris})
