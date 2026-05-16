#!/usr/bin/env python
"""Script de diagnostic pour vérifier les types de compte"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

print("\n" + "="*60)
print("DIAGNOSTIC DES TYPES DE COMPTE")
print("="*60 + "\n")

# Afficher tous les utilisateurs et leurs types de compte
users = User.objects.all()

if not users.exists():
    print("❌ Aucun utilisateur trouvé!")
else:
    print(f"✅ {users.count()} utilisateur(s) trouvé(s)\n")
    
    for user in users:
        try:
            profile = user.profile
            account_type = profile.account_type
            
            print(f"👤 Utilisateur: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Type de compte: {account_type}")
            
            # Vérifier s'il y a un profil professionnel
            try:
                prof_profile = profile.professionalprofile
                print(f"   ✅ Profil professionnel: {prof_profile.establishment_name}")
            except:
                print(f"   ❌ Pas de profil professionnel")
            
            print()
        except Exception as e:
            print(f"❌ Erreur pour {user.username}: {e}\n")

print("="*60)
