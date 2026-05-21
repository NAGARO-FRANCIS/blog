#!/usr/bin/env python
"""
Diagnostic pour le problème de publication d'annonces résidences
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.forms import LogementResidenceForm
from logement.models import Logement

# Simuler une résidence complète
test_data = {
    'titre': 'Studio moderne climatisé - Test Publication',
    'description': 'Un beau studio climatisé avec WiFi.',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'studio',
    
    # Caractéristiques du logement
    'surface': 45.5,
    'nombre_pieces': 2,
    'nombre_chambres': 1,
    'nombre_salles_bain': 1,
    'meuble': True,
    
    # Tarification résidence
    'prix_par_mois': 150000,
    'caution_mois': 2,
    'frais_agence': 50000,
    'duree_min_bail': '1 an',
    'type_charge': 'charges_comprises',
    'conditions_speciales': 'Pas d\'animaux',
    'disponible_depuis': '2026-05-21',
    
    # Équipements
    'climatisation': True,
    'wifi': True,
    'garage': False,
    'cuisine_equipee': True,
    'ascenseur': False,
    'gardien': False,
    'securite': False,
    'buanderie': False,
}

# Test 1: Valider le formulaire
print("=" * 80)
print("TEST 1: Validation du formulaire LogementResidenceForm")
print("=" * 80)

form = LogementResidenceForm(data=test_data)
print(f"\nFormulaire valide: {form.is_valid()}")

if not form.is_valid():
    print("\n❌ ERREURS DÉTECTÉES:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"  {field}: {error}")
    
    print("\n🔍 Champs obligatoires du formulaire:")
    for field_name, field in form.fields.items():
        print(f"  - {field_name}: required={field.required}, widget={field.widget.__class__.__name__}")
else:
    print("\n✅ Formulaire VALIDE!")
    
    # Test 2: Sauvegarder un exemple
    print("\n" + "=" * 80)
    print("TEST 2: Création d'une résidence de test")
    print("=" * 80)
    
    try:
        # Créer un utilisateur de test si n'existe pas
        test_user, created = User.objects.get_or_create(
            username='firmine_test',
            defaults={'email': 'firmine@test.com', 'first_name': 'Firmine'}
        )
        
        # Vérifier/créer le profil avec account_type='residence'
        profile, profile_created = Profile.objects.get_or_create(
            user=test_user,
            defaults={'account_type': 'residence', 'role': 'proprietaire'}
        )
        
        if not profile_created and profile.account_type != 'residence':
            profile.account_type = 'residence'
            profile.save()
        
        print(f"  Utilisateur test: {test_user.username}")
        print(f"  Account type: {profile.account_type}")
        
        # Sauvegarder le logement
        logement = form.save(commit=False)
        logement.proprietaire = test_user
        logement.account_type = 'residence'
        logement.prix = logement.prix_par_mois  # Définir prix depuis prix_par_mois
        logement.save()
        
        print(f"\n✅ Résidence créée avec succès!")
        print(f"  ID: {logement.id}")
        print(f"  Titre: {logement.titre}")
        print(f"  Prix/mois: {logement.prix_par_mois} FCFA")
        
        # Nettoyage
        logement.delete()
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()

# Test 3: Vérifier les champs manquants du modèle
print("\n" + "=" * 80)
print("TEST 3: Analyse des champs du modèle")
print("=" * 80)

logement_model = Logement._meta
print("\nChamps du modèle Logement:")
for field in logement_model.fields:
    required_in_model = not (field.null or field.blank)
    print(f"  - {field.name}: required={required_in_model}, null={field.null}, blank={field.blank}")

print("\n" + "=" * 80)
print("RÉSUMÉ DES PROBLÈMES")
print("=" * 80)
print("\nSi le formulaire n'est pas valide, chercher:")
print("1. Les champs obligatoires qui manquent une valeur par défaut")
print("2. Les validations personnalisées qui rejettent les données")
print("3. Les types de champs incompatibles")
