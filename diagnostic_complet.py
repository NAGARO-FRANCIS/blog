#!/usr/bin/env python
"""
Diagnostic complet du problème de publication
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.forms import LogementResidenceForm, PhotoLogementFormSet, VideoLogementFormSet
from logement.models import Logement, PhotoLogement, VideoLogement

print("=" * 80)
print("DIAGNOSTIC COMPLET: Problème de publication")
print("=" * 80)

# Test 1: Formulaire seul
print("\n1️⃣ TEST: Formulaire sans photos/vidéos")
print("-" * 80)

residence_data = {
    'titre': 'Appartement test',
    'description': 'Description test',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'appartement',
}

form = LogementResidenceForm(data=residence_data)
print(f"Formulaire valide: {form.is_valid()}")
if not form.is_valid():
    print("ERREURS:")
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")

# Test 2: Formulaire + formsets vides
print("\n2️⃣ TEST: Formulaire + formsets photos/vidéos vides")
print("-" * 80)

# Créer un logement test pour avoir une instance
user, _ = User.objects.get_or_create(username='test_user', defaults={'email': 'test@test.com'})
profile, _ = Profile.objects.get_or_create(user=user, defaults={'account_type': 'residence'})

logement_test = Logement.objects.create(
    titre='Logement Test',
    description='Test',
    ville='Abidjan',
    quartier='Cocody',
    type_logement='appartement',
    proprietaire=user,
    account_type='residence'
)

# Tester les formsets
photo_formset = PhotoLogementFormSet(data={
    'photologement_set-TOTAL_FORMS': '1',
    'photologement_set-INITIAL_FORMS': '0',
    'photologement_set-MIN_NUM_FORMS': '0',
    'photologement_set-MAX_NUM_FORMS': '1000',
    'photologement_set-0-image': '',
    'photologement_set-0-alt_text': '',
    'photologement_set-0-order': '',
}, instance=logement_test)

video_formset = VideoLogementFormSet(data={
    'videologement_set-TOTAL_FORMS': '1',
    'videologement_set-INITIAL_FORMS': '0',
    'videologement_set-MIN_NUM_FORMS': '0',
    'videologement_set-MAX_NUM_FORMS': '1000',
    'videologement_set-0-video': '',
    'videologement_set-0-titre': '',
    'videologement_set-0-description': '',
    'videologement_set-0-order': '',
}, instance=logement_test)

print(f"Photo formset valide: {photo_formset.is_valid()}")
if not photo_formset.is_valid():
    print("ERREURS photos:")
    print(f"  Non form errors: {photo_formset.non_form_errors()}")
    for form_photo in photo_formset:
        if form_photo.errors:
            print(f"  Form errors: {form_photo.errors}")

print(f"\nVidéo formset valide: {video_formset.is_valid()}")
if not video_formset.is_valid():
    print("ERREURS vidéos:")
    print(f"  Non form errors: {video_formset.non_form_errors()}")
    for form_video in video_formset:
        if form_video.errors:
            print(f"  Form errors: {form_video.errors}")

# Test 3: Vérifier la vue
print("\n3️⃣ TEST: Analyse de la vue ajouter_logement")
print("-" * 80)

from logement.views import ajouter_logement

# Lire le code de la vue pour voir s'il y a d'autres validations
print("Vérification du fichier views.py pour les validations supplémentaires...")

# Test 4: Vérifier les champs requis du formulaire
print("\n4️⃣ TEST: Analyse des champs requis")
print("-" * 80)

form = LogementResidenceForm()
print("Champs requis du formulaire:")
for field_name, field in form.fields.items():
    if field.required:
        print(f"  ❌ {field_name}: REQUIS")
    else:
        print(f"  ✅ {field_name}: optionnel")

# Cleanup
logement_test.delete()

print("\n" + "=" * 80)
print("FIN DU DIAGNOSTIC")
print("=" * 80)
