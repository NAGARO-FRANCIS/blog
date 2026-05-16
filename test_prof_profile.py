#!/usr/bin/env python
"""Script pour tester manuellement la création d'un ProfessionalProfile"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

print("\n" + "="*60)
print("TEST DE CRÉATION MANUELLE DE PROFESSIONALPROFILE")
print("="*60 + "\n")

# Chercher l'utilisateur Louise
try:
    louise = User.objects.get(username='louise')
    print(f"✅ Utilisateur trouvé: {louise.username}")
    print(f"   Email: {louise.email}")
    
    # Vérifier le profile
    try:
        profile = louise.profile
        print(f"\n✅ Profile trouvé:")
        print(f"   Type: {profile.account_type}")
        print(f"   Rôle: {profile.role}")
    except Exception as e:
        print(f"❌ Erreur profile: {e}")
    
    # Vérifier le ProfessionalProfile
    try:
        prof_profile = louise.profile.professionalprofile
        print(f"\n✅ ProfessionalProfile trouvé:")
        print(f"   Établissement: {prof_profile.establishment_name}")
        print(f"   Type: {prof_profile.establishment_type}")
    except Exception as e:
        print(f"\n❌ Pas de ProfessionalProfile: {e}")
        
        # Essayer de le créer
        print("\n🔧 Tentative de création du ProfessionalProfile...")
        try:
            prof_profile = ProfessionalProfile.objects.create(
                profile=louise.profile,
                establishment_type='residence',
                establishment_name='Résidence Test Louise',
                siret_or_rccm='CI123456789',
                legal_representative=f"{louise.first_name} {louise.last_name}",
                legal_phone=louise.profile.telephone or '+225 00 00 00 00',
                establishment_address='Test Address',
                establishment_city=louise.profile.ville or 'Abidjan',
                number_of_rooms=5,
            )
            print(f"✅ ProfessionalProfile créé avec succès!")
            print(f"   Établissement: {prof_profile.establishment_name}")
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")

except User.DoesNotExist:
    print("❌ Utilisateur louise non trouvé")

print("\n" + "="*60)
