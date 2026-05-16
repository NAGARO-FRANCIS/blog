#!/usr/bin/env python
"""Vérifier l'état complet des dashboards"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

print("\n" + "="*70)
print("VÉRIFICATION COMPLÈTE DES DASHBOARDS")
print("="*70 + "\n")

# Compter les utilisateurs par type
individu_count = Profile.objects.filter(account_type='individu').count()
residence_count = Profile.objects.filter(account_type='residence').count()
hotel_count = Profile.objects.filter(account_type='hotel').count()

print(f"📊 STATISTIQUES DES COMPTES:")
print(f"   Individu: {individu_count}")
print(f"   Résidence: {residence_count}")
print(f"   Hôtel: {hotel_count}")

# Vérifier les ProfessionalProfiles
prof_count = ProfessionalProfile.objects.count()
print(f"\n📊 PROFILS PROFESSIONNELS:")
print(f"   Total ProfessionalProfile: {prof_count}")

# Vérifier les détails des résidences et hôtels
print(f"\n📍 DÉTAILS DES ÉTABLISSEMENTS:")
for prof in ProfessionalProfile.objects.all():
    print(f"   - {prof.establishment_name}")
    print(f"     Type: {prof.establishment_type}")
    print(f"     Propriétaire: {prof.profile.user.username}")
    print()

# Vérifier les routes URL
print("\n📍 VÉRIFICATION DES ROUTES URL:")
try:
    from django.urls import reverse
    
    print(f"   Dashboard router: {reverse('accounts:dashboard')}")
    print(f"   Dashboard individu: {reverse('accounts:dashboard_individu')}")
    print(f"   Dashboard résidence: {reverse('accounts:dashboard_residence')}")
    print(f"   Dashboard hôtel: {reverse('accounts:dashboard_hotel')}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "="*70)
