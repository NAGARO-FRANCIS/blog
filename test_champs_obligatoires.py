#!/usr/bin/env python
"""
Test pour identifier quel champ obligatoire cause le problème
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.forms import LogementResidenceForm

# Test 1: Sans surface (optionnel selon le modèle mais requis selon le template)
print("=" * 80)
print("Test 1: Sans surface")
print("=" * 80)

test_data_1 = {
    'titre': 'Studio moderne climatisé',
    'description': 'Un beau studio climatisé avec WiFi.',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
    'surface': '',  # VIDE
    'nombre_pieces': 2,
    'nombre_chambres': 1,
    'nombre_salles_bain': 1,
    'meuble': True,
    'prix_par_mois': 150000,
    'caution_mois': 2,
    'frais_agence': 50000,
    'duree_min_bail': '1 an',
    'type_charge': 'charges_comprises',
    'conditions_speciales': 'Pas d\'animaux',
}

form = LogementResidenceForm(data=test_data_1)
print(f"Formulaire valide sans surface: {form.is_valid()}")
if not form.is_valid():
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")

# Test 2: Avec surface (OK)
print("\n" + "=" * 80)
print("Test 2: Avec surface")
print("=" * 80)

test_data_2 = {
    'titre': 'Studio moderne climatisé',
    'description': 'Un beau studio climatisé avec WiFi.',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
    'surface': 45.5,
    'nombre_pieces': 2,
    'nombre_chambres': 1,
    'nombre_salles_bain': 1,
    'meuble': True,
    'prix_par_mois': 150000,
    'caution_mois': 2,
    'frais_agence': 50000,
    'duree_min_bail': '1 an',
    'type_charge': 'charges_comprises',
    'conditions_speciales': 'Pas d\'animaux',
}

form = LogementResidenceForm(data=test_data_2)
print(f"Formulaire valide avec surface: {form.is_valid()}")
if not form.is_valid():
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")

# Test 3: Nombre_pieces vide
print("\n" + "=" * 80)
print("Test 3: Sans nombre_pieces")
print("=" * 80)

test_data_3 = {
    'titre': 'Studio moderne climatisé',
    'description': 'Un beau studio climatisé avec WiFi.',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
    'surface': 45.5,
    'nombre_pieces': '',  # VIDE
    'nombre_chambres': 1,
    'nombre_salles_bain': 1,
    'meuble': True,
    'prix_par_mois': 150000,
    'caution_mois': 2,
    'frais_agence': 50000,
    'duree_min_bail': '1 an',
    'type_charge': 'charges_comprises',
    'conditions_speciales': 'Pas d\'animaux',
}

form = LogementResidenceForm(data=test_data_3)
print(f"Formulaire valide sans nombre_pieces: {form.is_valid()}")
if not form.is_valid():
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")

# Test 4: Nombre_pieces = 0
print("\n" + "=" * 80)
print("Test 4: nombre_pieces = 0")
print("=" * 80)

test_data_4 = {
    'titre': 'Studio moderne climatisé',
    'description': 'Un beau studio climatisé avec WiFi.',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
    'surface': 45.5,
    'nombre_pieces': 0,  # ZÉRO
    'nombre_chambres': 1,
    'nombre_salles_bain': 1,
    'meuble': True,
    'prix_par_mois': 150000,
    'caution_mois': 2,
    'frais_agence': 50000,
    'duree_min_bail': '1 an',
    'type_charge': 'charges_comprises',
    'conditions_speciales': 'Pas d\'animaux',
}

form = LogementResidenceForm(data=test_data_4)
print(f"Formulaire valide avec nombre_pieces = 0: {form.is_valid()}")
if not form.is_valid():
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")
