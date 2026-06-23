#!/usr/bin/env python
"""Script pour corriger le compte résidence de mamadou"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

print("\n" + "="*70)
print("CORRECTION DU PROFIL DE MAMADOU")
print("="*70 + "\n")

try:
    # Trouver l'utilisateur mamadou
    mamadou = User.objects.get(username='mamadou')
    profile = mamadou.profile
    
    print(f"✅ Utilisateur trouvé: {mamadou.username}")
    print(f"   Email: {mamadou.email}")
    print(f"   Account type ACTUEL: {profile.account_type}")
    print(f"   Role ACTUEL: {profile.role}")
    
    # Corriger le account_type
    if profile.account_type != 'residence':
        print(f"\n🔧 Correction de account_type: '{profile.account_type}' → 'residence'")
        profile.account_type = 'residence'
        profile.role = 'proprietaire'  # Mettre à jour le rôle aussi
        profile.save()
        print(f"   ✅ Profil mis à jour avec succès!")
    else:
        print(f"\n✅ Account type est déjà 'residence'")
    
    # Vérifier/créer le ProfessionalProfile
    try:
        prof_profile = profile.professional_profile
        print(f"\n✅ ProfessionalProfile existe déjà:")
        print(f"   Établissement: {prof_profile.establishment_name}")
        print(f"   Type: {prof_profile.establishment_type}")
    except:
        print(f"\n⚠️  ProfessionalProfile n'existe pas")
        print(f"🔧 Création automatique du ProfessionalProfile...")
        
        # Créer un ProfessionalProfile par défaut
        prof_profile = ProfessionalProfile.objects.create(
            profile=profile,
            establishment_type='residence',
            establishment_name=f"Résidence de {mamadou.first_name or mamadou.username}",
            siret_or_rccm='TO_BE_COMPLETED',
            legal_representative=mamadou.get_full_name() or mamadou.username,
            legal_phone=profile.telephone or '+225 00 00 00 00',
            establishment_address='Adresse à compléter',
            establishment_city=profile.ville or 'Abidjan',
            number_of_rooms=0,
        )
        
        print(f"   ✅ ProfessionalProfile créé avec succès!")
        print(f"   Établissement: {prof_profile.establishment_name}")
        print(f"   ID: {prof_profile.id}")
        print(f"\n   ⚠️  Attention: SIRET/RCCM est provisoire. À compléter par l'utilisateur dans son profil!")
    
    print(f"\n" + "="*70)
    print("✅ CORRECTION TERMINÉE - L'utilisateur peut maintenant se reconnecter")
    print("="*70 + "\n")
    
except User.DoesNotExist:
    print(f"❌ Erreur: L'utilisateur 'mamadou' n'existe pas!")
    print(f"\nListe des utilisateurs existants:")
    for user in User.objects.all():
        print(f"   - {user.username} ({user.email})")

except Exception as e:
    print(f"❌ Erreur lors de la correction: {e}")
    import traceback
    traceback.print_exc()
