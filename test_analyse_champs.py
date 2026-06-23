#!/usr/bin/env python
"""
Test pour identifier tous les champs obligatoires problématiques
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.forms import LogementResidenceForm

# Test tous les champs obligatoires
print("=" * 80)
print("Analyse des champs du formulaire LogementResidenceForm")
print("=" * 80)

form = LogementResidenceForm()
print("\nChamps obligatoires (required=True):")
for field_name, field in form.fields.items():
    if field.required:
        print(f"  - {field_name}: {field.widget.__class__.__name__}, label={field.label}")

print("\nChamps optionnels (required=False):")
for field_name, field in form.fields.items():
    if not field.required:
        print(f"  - {field_name}: {field.widget.__class__.__name__}, label={field.label}")

# Test des champs qui ont NumberInput
print("\n" + "=" * 80)
print("Test des champs NumberInput")
print("=" * 80)

number_fields = ['surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain', 'etage', 'prix_par_mois', 'caution_mois', 'frais_agence']

for field_name in number_fields:
    if field_name in form.fields:
        field = form.fields[field_name]
        print(f"\n{field_name}:")
        print(f"  - required: {field.required}")
        print(f"  - widget: {field.widget.__class__.__name__}")
        
        # Test avec valeur vide
        test_data = {
            'titre': 'Test',
            'description': 'Test',
            'ville': 'Test',
            'type_logement': 'studio',
            field_name: '',
        }
        test_form = LogementResidenceForm(data=test_data)
        
        # Vérifier juste la validation du champ
        field_valid = True
        if not test_form.is_valid():
            if field_name in test_form.errors:
                field_valid = False
                print(f"  - Erreur avec valeur vide: {test_form.errors[field_name]}")
        
        if field_valid:
            print(f"  - ✓ Accepte les valeurs vides")
