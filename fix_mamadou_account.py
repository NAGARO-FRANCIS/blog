#!/usr/bin/env python
"""
Commande Django pour corriger les comptes avec le mauvais account_type.
Usage: python manage.py fix_account_type mamadou residence
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

def fix_account_type(username, correct_type):
    """Corrige le account_type d'un utilisateur"""
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        
        print(f"\n{'='*70}")
        print(f"CORRECTION DU PROFIL : {username}")
        print(f"{'='*70}\n")
        
        print(f"Utilisateur: {user.username} ({user.email})")
        print(f"Nom complet: {user.get_full_name()}")
        print(f"Account type ACTUEL: {profile.account_type}")
        print(f"Rôle ACTUEL: {profile.role}")
        
        # Correction
        if profile.account_type != correct_type:
            profile.account_type = correct_type
            if correct_type in ['residence', 'hotel']:
                profile.role = 'proprietaire'
            profile.save()
            print(f"\n✅ Account type corrigé: {correct_type}")
            print(f"✅ Rôle mis à jour: {profile.role}")
        else:
            print(f"\n✅ Account type est déjà correct: {correct_type}")
        
        # Vérifier/créer ProfessionalProfile si nécessaire
        if correct_type in ['residence', 'hotel']:
            try:
                prof_profile = profile.professional_profile
                print(f"✅ ProfessionalProfile existe: {prof_profile.establishment_name}")
            except:
                print(f"\n🔧 Création du ProfessionalProfile...")
                prof_profile = ProfessionalProfile.objects.create(
                    profile=profile,
                    establishment_type=correct_type,
                    establishment_name=f"{correct_type.capitalize()} de {user.get_full_name() or user.username}",
                    siret_or_rccm='TO_BE_COMPLETED',
                    legal_representative=user.get_full_name() or user.username,
                    legal_phone=profile.telephone or '+225 00 00 00 00',
                    establishment_address='À compléter',
                    establishment_city=profile.ville or 'Abidjan',
                    number_of_rooms=0,
                )
                print(f"✅ ProfessionalProfile créé: {prof_profile.establishment_name}")
        
        print(f"\n{'='*70}")
        print(f"✅ CORRECTION RÉUSSIE")
        print(f"{'='*70}\n")
        return True
        
    except User.DoesNotExist:
        print(f"❌ Utilisateur '{username}' introuvable")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Pour mamadou
    fix_account_type('mamadou', 'residence')
