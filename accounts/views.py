# accounts/views.py
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Profile
from .forms import SignUpForm, ProfileEditForm


def inscription(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)  # ← ajouter FILES pour la photo
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
            profile.type_piece_identite = form.cleaned_data.get('type_piece_identite', '')
            profile.numero_piece_identite = form.cleaned_data.get('numero_piece_identite', '')
            if 'photo_profil' in request.FILES:
                profile.photo_profil = request.FILES['photo_profil']
            profile.save()

            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'accounts/inscription.html', {'form': form})


@login_required
def profil(request):  # ← une seule fonction profil
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Compteurs — adapter les related_name selon vos modèles
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