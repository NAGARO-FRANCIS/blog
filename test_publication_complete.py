#!/usr/bin/env python
"""
Test complet: Publication complète (formulaire + formsets)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.forms import LogementResidenceForm, PhotoLogementFormSet, VideoLogementFormSet
from logement.models import Logement

print("=" * 80)
print("TEST COMPLET: Publication Résidence (formulaire + formsets)")
print("=" * 80)

# Données du formulaire
residence_data = {
    'titre': 'Bel appartement 2 pièces climatisé - TEST COMPLET',
    'description': 'Un bel appartement moderne avec climatisation',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'appartement',
}

# Données des formsets
photo_data = {
    'photos-TOTAL_FORMS': '1',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    'photos-0-image': '',
    'photos-0-alt_text': '',
    'photos-0-order': '',
}

video_data = {
    'videos-TOTAL_FORMS': '1',
    'videos-INITIAL_FORMS': '0',
    'videos-MIN_NUM_FORMS': '0',
    'videos-MAX_NUM_FORMS': '1000',
    'videos-0-video': '',
    'videos-0-titre': '',
    'videos-0-description': '',
    'videos-0-order': '',
}

# Test 1: Valider le formulaire
print("\n1️⃣ Validation du formulaire principal")
form = LogementResidenceForm(data=residence_data)
print(f"Formulaire valide: {form.is_valid()}")
if not form.is_valid():
    print("ERREURS:")
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")
    sys.exit(1)

# Test 2: Créer un utilisateur et un logement temporaire
print("\n2️⃣ Création du logement temporaire")
user, _ = User.objects.get_or_create(username='firmine_test_complet', defaults={'email': 'firmine@test.com', 'first_name': 'Firmine'})
profile, _ = Profile.objects.get_or_create(user=user, defaults={'account_type': 'residence', 'role': 'proprietaire'})

# Créer le logement d'abord pour les formsets
logement = Logement.objects.create(
    titre='Temp',
    description='Temp',
    ville='Abidjan',
    quartier='Cocody',
    type_logement='appartement',
    proprietaire=user,
    account_type='residence'
)

# Test 3: Valider les formsets
print("\n3️⃣ Validation des formsets")

photo_formset = PhotoLogementFormSet(data=photo_data, instance=logement, prefix='photos')
print(f"Photo formset valide: {photo_formset.is_valid()}")
if not photo_formset.is_valid():
    print("ERREURS photos:")
    print(f"  Non form errors: {photo_formset.non_form_errors()}")
    for form_photo in photo_formset:
        if form_photo.errors:
            print(f"  Form errors: {form_photo.errors}")
    sys.exit(1)

video_formset = VideoLogementFormSet(data=video_data, instance=logement, prefix='videos')
print(f"Video formset valide: {video_formset.is_valid()}")
if not video_formset.is_valid():
    print("ERREURS vidéos:")
    print(f"  Non form errors: {video_formset.non_form_errors()}")
    for form_video in video_formset:
        if form_video.errors:
            print(f"  Form errors: {form_video.errors}")
    sys.exit(1)

# Test 4: Sauvegarder le logement avec les données nettoyées
print("\n4️⃣ Sauvegarde du logement")
logement_final = form.save(commit=False)
logement_final.proprietaire = user
logement_final.account_type = 'residence'
logement_final.prix = logement_final.prix_par_mois
logement_final.save()

print(f"✅ Logement sauvegardé avec succès!")
print(f"  ID: {logement_final.id}")
print(f"  Titre: {logement_final.titre}")
print(f"  Propriétaire: {logement_final.proprietaire.username}")
print(f"  Type: {logement_final.account_type}")

# Cleanup
logement.delete()
logement_final.delete()

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ Publication complète fonctionnelle!")
print("   - Formulaire principal: ✅")
print("   - Formset photos: ✅")
print("   - Formset vidéos: ✅")
print("   - Sauvegarde: ✅")
print("\nFiremine peut maintenant publier ses annonces! 🎉")
