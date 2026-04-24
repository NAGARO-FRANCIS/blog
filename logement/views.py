from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .forms import LogementForm, RechercheLogementForm, PhotoLogementFormSet
from .models import Logement


def home(request):
    form = RechercheLogementForm(request.GET or None)
    logements = Logement.objects.prefetch_related('photos').order_by('-created_at')

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
            logements = logements.filter(prix__lte=prix_max)
        if type_logement:
            logements = logements.filter(type_logement=type_logement)

    return render(request, 'acceuil.html', {'form': form, 'logements': logements})


@login_required
@require_http_methods(["GET", "POST"])
def ajouter_logement(request):
    if request.method == 'POST':
        form = LogementForm(request.POST)
        formset = PhotoLogementFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            logement = form.save(commit=False)
            logement.proprietaire = request.user
            logement.save()
            
            # Sauvegarder les photos
            formset.instance = logement
            formset.save()
            
            return redirect('home')
    else:
        form = LogementForm()
        formset = PhotoLogementFormSet()

    return render(request, 'ajouter_logement.html', {
        'form': form,
        'formset': formset,
    })
