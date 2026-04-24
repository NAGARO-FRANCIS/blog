import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ivoire.settings")
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

print("=" * 60)
print("VÉRIFICATION DES PROFILS")
print("=" * 60)

profiles = Profile.objects.all()
print(f"\nTotal de profils: {profiles.count()}")
print("\nÉtat de vérification:")
print("-" * 60)

for profile in profiles:
    print(f"Profil ID: {profile.id} | User: {profile.user.username} | Vérifié: {profile.verified}")

print("\n" + "-" * 60)
print("Mise à jour de tous les profils à verified=True...")
count = profiles.count()
profiles.update(verified=True)
print(f"✓ {count} profils mis à jour")

print("\n" + "-" * 60)
print("État final:")
print("-" * 60)
for profile in Profile.objects.all():
    print(f"Profil ID: {profile.id} | User: {profile.user.username} | Vérifié: {profile.verified}")
print("=" * 60)
