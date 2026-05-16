#!/usr/bin/env python
"""Script pour créer le ProfessionalProfile manquant pour Louise"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

print("\n" + "="*60)
print("CRÉATION DU PROFESSIONALPROFILE MANQUANT")
print("="*60 + "\n")

try:
    louise = User.objects.get(username='Louise')
    profile = louise.profile
    
    print(f"✅ Utilisateur trouvé: {louise.username}")
    print(f"   Type de compte: {profile.account_type}")
    
    # Vérifier si ProfessionalProfile existe déjà
    try:
        prof_profile = profile.professionalprofile
        print(f"\n✅ ProfessionalProfile existe déjà: {prof_profile.establishment_name}")
    except:
        print(f"\n🔧 Création d'un ProfessionalProfile...")
        
        prof_profile = ProfessionalProfile.objects.create(
            profile=profile,
            establishment_type='residence',
            establishment_name='Résidence Louise',
            siret_or_rccm='TEMP-LOUISE-001',
            legal_representative=f"{louise.first_name} {louise.last_name}",
            legal_phone=profile.telephone or '+225 00 00 00 00',
            establishment_address='Adresse temporaire',
            establishment_city=profile.ville or 'Abidjan',
            number_of_rooms=5,
        )
        
        print(f"✅ ProfessionalProfile créé avec succès!")
        print(f"   Établissement: {prof_profile.establishment_name}")
        print(f"   Type: {prof_profile.establishment_type}")
        print(f"   Salons/Chambres: {prof_profile.number_of_rooms}")

except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "="*60)
