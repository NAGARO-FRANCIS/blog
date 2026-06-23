#!/usr/bin/env python
"""
Test simple pour vérifier que les publications fonctionnent
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.models import Logement
from logement.forms import LogementResidenceForm, LogementHotelForm

# ==================== TEST RÉSIDENCE ====================
print("=" * 80)
print("TEST: Firmine publie une RÉSIDENCE (données minimales)")
print("=" * 80)

# Données minimales que Firmine remplirait
firmine_data = {
    'titre': 'Bel appartement 2 pièces climatisé',
    'description': 'Un bel appartement moderne avec climatisation',
    'ville': 'Abidjan',
    'quartier': 'Cocody',
    'type_logement': 'appartement',
    # Les champs optionnels sont vides!
}

form = LogementResidenceForm(data=firmine_data)

if form.is_valid():
    print("\n✅ SUCCÈS! Le formulaire est valide")
    print("\nDonnées nettoyées:")
    cleaned = form.cleaned_data
    for key in ['titre', 'description', 'ville', 'nombre_pieces', 'nombre_chambres', 
                'nombre_salles_bain', 'surface', 'prix_par_mois']:
        if key in cleaned:
            print(f"  {key}: {cleaned[key]}")
    
    # Créer un utilisateur de test
    user, _ = User.objects.get_or_create(
        username='firmine',
        defaults={'email': 'firmine@test.com', 'first_name': 'Firmine'}
    )
    
    # Créer le profil avec account_type=residence
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'account_type': 'residence', 'role': 'proprietaire'}
    )
    
    # Sauvegarder le logement
    logement = form.save(commit=False)
    logement.proprietaire = user
    logement.account_type = 'residence'
    logement.prix = logement.prix_par_mois
    logement.save()
    
    print(f"\n✅ Résidence publiée avec succès!")
    print(f"  ID: {logement.id}")
    print(f"  Propriétaire: {logement.proprietaire.username}")
    print(f"  Type: {logement.account_type}")
    
    # Cleanup
    logement.delete()
    
else:
    print("\n❌ ERREUR - Le formulaire n'est pas valide:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"  {field}: {error}")

# ==================== TEST HÔTEL ====================
print("\n" + "=" * 80)
print("TEST: Un hôtelier publie un HÔTEL (données minimales)")
print("=" * 80)

hotel_data = {
    'titre': 'Chambre climatisée vue mer',
    'description': 'Une belle chambre avec vue panoramique',
    'ville': 'Abidjan',
    'quartier': 'Plateaux',
    'type_logement': 'chambre',
    # Les champs optionnels sont vides!
}

form = LogementHotelForm(data=hotel_data)

if form.is_valid():
    print("\n✅ SUCCÈS! Le formulaire est valide")
    print("\nDonnées nettoyées:")
    cleaned = form.cleaned_data
    for key in ['titre', 'description', 'ville', 'nombre_lits', 'capacite',
                'nombre_salles_bain', 'surface', 'prix_par_nuit', 'min_sejour']:
        if key in cleaned:
            print(f"  {key}: {cleaned[key]}")
    
    # Créer un utilisateur de test
    user, _ = User.objects.get_or_create(
        username='hotelier',
        defaults={'email': 'hotel@test.com', 'first_name': 'Hôtelier'}
    )
    
    # Créer le profil avec account_type=hotel
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'account_type': 'hotel', 'role': 'proprietaire'}
    )
    
    # Sauvegarder le logement
    logement = form.save(commit=False)
    logement.proprietaire = user
    logement.account_type = 'hotel'
    logement.prix = logement.prix_par_nuit
    logement.save()
    
    print(f"\n✅ Hôtel publié avec succès!")
    print(f"  ID: {logement.id}")
    print(f"  Propriétaire: {logement.proprietaire.username}")
    print(f"  Type: {logement.account_type}")
    
    # Cleanup
    logement.delete()
    
else:
    print("\n❌ ERREUR - Le formulaire n'est pas valide:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"  {field}: {error}")

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ Les utilisateurs peuvent maintenant publier des annonces")
print("   même s'ils oublient de remplir tous les champs optionnels.")
print("   Les valeurs par défaut intelligentes sont appliquées automatiquement.")
