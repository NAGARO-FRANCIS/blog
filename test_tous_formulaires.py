#!/usr/bin/env python
"""
Test complet des formulaires après corrections
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.forms import LogementHotelForm, LogementResidenceForm, LogementProprietaireForm, LogementColocataireForm

# Données de test minimales (uniquement les champs obligatoires du modèle)
minimal_data = {
    'titre': 'Test publication minimale',
    'description': 'Une annonce simple',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
}

print("=" * 80)
print("TEST: Soumission minimale avec champs optionnels vides")
print("=" * 80)

# Test LogementResidenceForm
print("\n1️⃣ LogementResidenceForm (RÉSIDENCE)")
form = LogementResidenceForm(data=minimal_data)
if form.is_valid():
    print("   ✅ VALIDE - Les champs optionnels ont été remplis avec des valeurs par défaut")
    # Vérifier les valeurs par défaut
    cleaned = form.cleaned_data
    print(f"      - nombre_pieces: {cleaned.get('nombre_pieces')}")
    print(f"      - nombre_chambres: {cleaned.get('nombre_chambres')}")
    print(f"      - nombre_salles_bain: {cleaned.get('nombre_salles_bain')}")
    print(f"      - surface: {cleaned.get('surface')}")
    print(f"      - prix_par_mois: {cleaned.get('prix_par_mois')}")
else:
    print("   ❌ ERREUR:")
    for field, errors in form.errors.items():
        print(f"      - {field}: {errors}")

# Test LogementHotelForm
print("\n2️⃣ LogementHotelForm (HÔTEL)")
form = LogementHotelForm(data=minimal_data)
if form.is_valid():
    print("   ✅ VALIDE - Les champs optionnels ont été remplis avec des valeurs par défaut")
    cleaned = form.cleaned_data
    print(f"      - nombre_lits: {cleaned.get('nombre_lits')}")
    print(f"      - capacite: {cleaned.get('capacite')}")
    print(f"      - nombre_salles_bain: {cleaned.get('nombre_salles_bain')}")
    print(f"      - prix_par_nuit: {cleaned.get('prix_par_nuit')}")
    print(f"      - min_sejour: {cleaned.get('min_sejour')}")
else:
    print("   ❌ ERREUR:")
    for field, errors in form.errors.items():
        print(f"      - {field}: {errors}")

# Test LogementProprietaireForm
print("\n3️⃣ LogementProprietaireForm (PROPRIÉTAIRE INDIVIDUEL)")
form = LogementProprietaireForm(data=minimal_data)
if form.is_valid():
    print("   ✅ VALIDE - Les champs optionnels ont été remplis avec des valeurs par défaut")
    cleaned = form.cleaned_data
    print(f"      - nombre_pieces: {cleaned.get('nombre_pieces')}")
    print(f"      - nombre_chambres: {cleaned.get('nombre_chambres')}")
    print(f"      - nombre_salles_bain: {cleaned.get('nombre_salles_bain')}")
    print(f"      - surface: {cleaned.get('surface')}")
    print(f"      - prix: {cleaned.get('prix')}")
else:
    print("   ❌ ERREUR:")
    for field, errors in form.errors.items():
        print(f"      - {field}: {errors}")

# Test LogementColocataireForm
print("\n4️⃣ LogementColocataireForm (COLOCATAIRE)")
form = LogementColocataireForm(data=minimal_data)
if form.is_valid():
    print("   ✅ VALIDE - Les champs optionnels ont été remplis avec des valeurs par défaut")
    cleaned = form.cleaned_data
    print(f"      - nombre_pieces: {cleaned.get('nombre_pieces')}")
    print(f"      - nombre_chambres: {cleaned.get('nombre_chambres')}")
    print(f"      - nombre_lits: {cleaned.get('nombre_lits')}")
    print(f"      - nombre_salles_bain: {cleaned.get('nombre_salles_bain')}")
    print(f"      - surface: {cleaned.get('surface')}")
    print(f"      - prix: {cleaned.get('prix')}")
else:
    print("   ❌ ERREUR:")
    for field, errors in form.errors.items():
        print(f"      - {field}: {errors}")

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ Tous les formulaires devraient maintenant accepter les publications")
print("   même si l'utilisateur oublie de remplir les champs optionnels.")
