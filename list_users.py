#!/usr/bin/env python
"""Script pour afficher tous les usernames"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, ProfessionalProfile

print("\n" + "="*60)
print("TOUS LES USERNAMES")
print("="*60 + "\n")

for user in User.objects.all():
    print(f"- {user.username}")

# Chercher un utilisateur avec "Louise" dans le nom
print("\n" + "="*60)
print("RECHERCHE DES UTILISATEURS 'RESIDENCE' OU 'HOTEL'")
print("="*60 + "\n")

from django.db.models import Q

users = User.objects.filter(
    Q(profile__account_type='residence') | Q(profile__account_type='hotel')
)

if users.exists():
    for user in users:
        profile = user.profile
        print(f"👤 {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Type: {profile.account_type}")
        print(f"   Professionnel Profile existe: {hasattr(profile, 'professionalprofile')}")
        print()
else:
    print("Aucun utilisateur residence/hotel trouvé")

print("="*60)
