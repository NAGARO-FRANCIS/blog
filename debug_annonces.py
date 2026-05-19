#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.models import Logement
from accounts.models import Profile
from django.contrib.auth.models import User

print("=" * 60)
print("VÉRIFICATION DES ANNONCES")
print("=" * 60)

print("\n📊 COMPTES DES ANNONCES:")
print(f"Total annonces: {Logement.objects.count()}")
print(f"Annonces hôtel: {Logement.objects.filter(account_type='hotel').count()}")
print(f"Annonces résidence: {Logement.objects.filter(account_type='residence').count()}")
print(f"Annonces individu: {Logement.objects.filter(account_type='individu').count()}")

print("\n📋 DÉTAIL DES ANNONCES:")
for logement in Logement.objects.all()[:10]:
    print(f"\n- Titre: {logement.titre}")
    print(f"  Type: {logement.account_type}")
    print(f"  Propriétaire: {logement.proprietaire}")
    if logement.proprietaire:
        try:
            profile = logement.proprietaire.profile
            print(f"  Rôle propriétaire: {profile.role}")
            print(f"  Type compte propriétaire: {profile.account_type}")
        except:
            print(f"  ⚠️ Pas de profil pour ce propriétaire")
    else:
        print(f"  ⚠️ Pas de propriétaire assigné!")

print("\n👥 COMPTES UTILISATEURS:")
for user in User.objects.all()[:5]:
    try:
        profile = user.profile
        print(f"\n- {user.username}: {profile.role} ({profile.account_type})")
    except:
        print(f"\n- {user.username}: ⚠️ Pas de profil")

print("\n" + "=" * 60)
