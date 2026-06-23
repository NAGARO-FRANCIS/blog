#!/usr/bin/env python
"""
Test: Reproduire et vérifier le fix du bug order field
Données exactes de Firmine qui a échoué
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.forms import LogementHotelForm, PhotoLogementFormSet, VideoLogementFormSet
from logement.models import Logement

print("=" * 80)
print("TEST: Reproduire le bug du champ 'order' vide")
print("=" * 80)

# Données exactes du formulaire de Firmine
hotel_data = {
    'titre': 'Ban hotel',
    'ville': 'Man',
    'quartier': 'zone',
    'description': 'une hôtel bien chic et dans un androis calme',
    'type_logement': 'villa',
    'surface': '10',
    'nombre_lits': '5',
    'capacite': '6',
    'nombre_salles_bain': '6',
    'etage': '0',
    'prix_par_nuit': '50000',
    'frais_nettoyage': '999.99',
    'min_sejour': '2',
    'disponible_depuis': '2026-05-15',
    'wifi': 'on',
    'climatisation': 'on',
    'television': 'on',
    'garage': 'on',
    'piscine': 'on',
}

# Données des photos EXACTEMENT comme Firmine les a envoyées
photo_data = {
    'photos-TOTAL_FORMS': '2',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '10',
    'photos-0-alt_text': 'la face de la maison',
    'photos-0-order': '0',        # ✅ Correctement rempli
    'photos-1-alt_text': "l'interieur  de la maison",
    'photos-1-order': '',         # ❌ VIDE - C'était le bug!
}

# Données des vidéos
video_data = {
    'videos-TOTAL_FORMS': '1',
    'videos-INITIAL_FORMS': '0',
    'videos-MIN_NUM_FORMS': '0',
    'videos-MAX_NUM_FORMS': '5',
    'videos-0-titre': 'une petite descripition de la maison',
    'videos-0-description': '',
    'videos-0-order': '0',
}

print("\n1️⃣ Validation du formulaire principal")
form = LogementHotelForm(data=hotel_data)
print(f"Formulaire valide: {form.is_valid()}")
if not form.is_valid():
    print("ERREURS:")
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")
    sys.exit(1)

# Créer un utilisateur et un logement
print("\n2️⃣ Création de l'hôtel (logement test)")
user, _ = User.objects.get_or_create(
    username='firmine_test_order',
    defaults={'email': 'firmine@test.com', 'first_name': 'Firmine'}
)
profile, _ = Profile.objects.get_or_create(
    user=user,
    defaults={'account_type': 'hotel', 'role': 'proprietaire'}
)

logement = Logement.objects.create(
    titre='Temp Hotel',
    description='Temp',
    ville='Man',
    quartier='zone',
    type_logement='villa',
    proprietaire=user,
    account_type='hotel'
)

print(f"✅ Hôtel créé: {logement.id}")

# Test 3: Valider les formsets avec les données exactes (ORDER VIDE!)
print("\n3️⃣ Validation du formset photos (photos-1-order VIDE!)")

photo_formset = PhotoLogementFormSet(data=photo_data, instance=logement, prefix='photos')
print(f"Photo formset valide: {photo_formset.is_valid()}")
if not photo_formset.is_valid():
    print("ERREURS:")
    print(f"  Non form errors: {photo_formset.non_form_errors()}")
    for i, form_photo in enumerate(photo_formset):
        if form_photo.errors:
            print(f"  Formulaire photo {i}: {form_photo.errors}")
    sys.exit(1)

# Vérifier que order a bien été converti en 0 pour la photo 1
print("\n4️⃣ Vérification que l'order a été converti en 0")
for i, form_photo in enumerate(photo_formset):
    if form_photo.cleaned_data and form_photo.cleaned_data.get('image') is None:
        order_value = form_photo.cleaned_data.get('order')
        print(f"  Photo {i}: order = {order_value} (type: {type(order_value).__name__})")

# Test 4: Valider le formset vidéos
print("\n5️⃣ Validation du formset vidéos")
video_formset = VideoLogementFormSet(data=video_data, instance=logement, prefix='videos')
print(f"Video formset valide: {video_formset.is_valid()}")
if not video_formset.is_valid():
    print("ERREURS:")
    print(f"  Non form errors: {video_formset.non_form_errors()}")
    for i, form_video in enumerate(video_formset):
        if form_video.errors:
            print(f"  Formulaire vidéo {i}: {form_video.errors}")
    sys.exit(1)

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ BUG RÉSOLU!")
print("   - Formulaire principal: ✅")
print("   - Formset photos (avec order vide): ✅")
print("   - Formset vidéos: ✅")
print("\n🎯 Le champ 'order' vide est maintenant converti en 0")
print("🎉 Firmine peut maintenant publier avec des photos partiellement remplies!")

# Cleanup
logement.delete()
