#!/usr/bin/env python
"""
Test final: Vérifier que les formsets acceptent maintenant les données
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.forms import PhotoLogementFormSet, VideoLogementFormSet
from logement.models import Logement, PhotoLogement, VideoLogement
from django.contrib.auth.models import User

# Créer un utilisateur et un logement de test
user, _ = User.objects.get_or_create(username='test_formset', defaults={'email': 'test@test.com'})
logement = Logement.objects.create(
    titre='Test Formsets',
    description='Test',
    ville='Abidjan',
    quartier='Cocody',
    type_logement='appartement',
    proprietaire=user,
    account_type='residence'
)

print("=" * 80)
print("TEST: Formsets avec prefixes")
print("=" * 80)

# Test 1: Données minimales avec management_form correct
print("\n1️⃣ Photos formset avec PREFIX 'photos'")

photo_data = {
    'photos-TOTAL_FORMS': '1',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    'photos-0-image': '',
    'photos-0-alt_text': '',
    'photos-0-order': '',
}

formset = PhotoLogementFormSet(data=photo_data, instance=logement, prefix='photos')
print(f"Photo formset valide: {formset.is_valid()}")
if not formset.is_valid():
    print("ERREURS:")
    print(f"  Non form errors: {formset.non_form_errors()}")
    for form_photo in formset:
        if form_photo.errors:
            print(f"  Form errors: {form_photo.errors}")
else:
    print("✅ SUCCÈS! Le formset accepte les données")

# Test 2: Vidéos formset
print("\n2️⃣ Vidéos formset avec PREFIX 'videos'")

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

formset = VideoLogementFormSet(data=video_data, instance=logement, prefix='videos')
print(f"Vidéo formset valide: {formset.is_valid()}")
if not formset.is_valid():
    print("ERREURS:")
    print(f"  Non form errors: {formset.non_form_errors()}")
    for form_video in formset:
        if form_video.errors:
            print(f"  Form errors: {form_video.errors}")
else:
    print("✅ SUCCÈS! Le formset accepte les données")

# Cleanup
logement.delete()

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ Les formsets devraient maintenant fonctionner correctement avec les prefixes!")
