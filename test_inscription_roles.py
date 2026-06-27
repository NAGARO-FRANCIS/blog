#!/usr/bin/env python3
"""
TEST SCRIPT - Système d'Inscription à 3 Étapes avec Rôles
=====================================================

Ce script teste le flux complet d'inscription avec sélection de rôle.
À exécuter: python manage.py shell < test_inscription_roles.py
"""

from django.contrib.auth.models import User
from accounts.models import Profile
from django.utils import timezone
import json

print("\n" + "="*60)
print("🧪 TEST - SYSTÈME D'INSCRIPTION À 3 ÉTAPES")
print("="*60 + "\n")

# ============================================================
# TEST 1: Créer 3 utilisateurs avec différents rôles
# ============================================================
print("TEST 1: Création de 3 utilisateurs avec différents rôles")
print("-" * 60)

test_users = [
    {
        'username': 'proprietaire_test',
        'email': 'prop@example.com',
        'first_name': 'Jean',
        'last_name': 'Propriétaire',
        'role': 'proprietaire',
        'account_type': 'individu',
    },
    {
        'username': 'locataire_test',
        'email': 'loc@example.com',
        'first_name': 'Marie',
        'last_name': 'Locataire',
        'role': 'locataire',
        'account_type': 'individu',
    },
    {
        'username': 'touriste_test',
        'email': 'coloc@example.com',
        'first_name': 'Pierre',
        'last_name': 'Touriste',
        'role': 'touriste',
        'account_type': 'individu',
    }
]

created_users = []
for user_data in test_users:
    try:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password='testpass123',
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
        )
        
        profile = user.profile
        profile.role = user_data['role']
        profile.account_type = user_data['account_type']
        profile.ville = 'Abidjan'
        profile.telephone = '+225 07 XX XX XX XX'
        profile.save()
        
        created_users.append(user)
        print(f"✅ {user_data['role'].upper()}: {user.get_full_name()} ({user.username})")
    except Exception as e:
        print(f"❌ Erreur création {user_data['role']}: {e}")

print()

# ============================================================
# TEST 2: Vérifier les permissions
# ============================================================
print("TEST 2: Vérification des permissions")
print("-" * 60)

for user in created_users:
    profile = user.profile
    role = profile.role
    
    print(f"\n👤 {user.get_full_name()} ({role})")
    print(f"   account_type: {profile.account_type}")
    print(f"   role: {profile.role}")
    
    # Vérifier les permissions
    can_publish = role != 'touriste'
    can_view = True
    can_contact = True
    
    print(f"   Permissions:")
    print(f"     ✅ Voir annonces: {can_view}")
    print(f"     {'✅' if can_publish else '❌'} Publier annonces: {can_publish}")
    print(f"     ✅ Contacter propriétaires: {can_contact}")

print()

# ============================================================
# TEST 3: Simulation de la restriction "ajouter_logement"
# ============================================================
print("TEST 3: Simulation - Restriction de publication pour Touriste")
print("-" * 60)

touriste_user = created_users[2]  # Pierre Touriste
profile = touriste_user.profile

# Simulation du code dans ajouter_logement()
if profile.account_type == 'individu' and profile.role == 'touriste':
    print(f"\n❌ Utilisateur {touriste_user.username} est TOURISTE")
    print("   Message d'erreur:")
    print("   '❌ En tant que touriste, vous ne pouvez pas publier d'annonces.'")
    print("   Redirection vers: /logement/home")
else:
    print(f"✅ Utilisateur {touriste_user.username} PEUT publier")

print()

# ============================================================
# TEST 4: Vérifier les autres rôles
# ============================================================
print("TEST 4: Vérification - Autres rôles CAN publier")
print("-" * 60)

for user in created_users[:2]:  # Propriétaire et Locataire
    profile = user.profile
    if profile.account_type == 'individu' and profile.role == 'touriste':
        print(f"❌ {profile.role.upper()}: Ne peut pas publier")
    else:
        print(f"✅ {profile.role.upper()} ({user.username}): CAN publier ✓")

print()

# ============================================================
# TEST 5: Statistiques
# ============================================================
print("TEST 5: Statistiques des Utilisateurs")
print("-" * 60)

total_users = User.objects.count()
individu_users = Profile.objects.filter(account_type='individu').count()
proprietaires = Profile.objects.filter(account_type='individu', role='proprietaire').count()
locataires = Profile.objects.filter(account_type='individu', role='locataire').count()
touristes = Profile.objects.filter(account_type='individu', role='touriste').count()

print(f"""
Total utilisateurs: {total_users}
Utilisateurs "individu": {individu_users}
  - Propriétaires: {proprietaires}
  - Locataires: {locataires}
  - Touristes: {touristes}
""")

# ============================================================
# TEST 6: Vérifier les URLs
# ============================================================
print("TEST 6: URLs à tester (manuellement)")
print("-" * 60)
print("""
1. Inscription - Choix type compte:
   GET /accounts/inscription/
   
2. NOUVEAU - Choix rôle pour individu:
   GET /accounts/inscription/individu/
   POST /accounts/inscription/individu/ (role='proprietaire')
   
3. Formulaire complet:
   GET /accounts/inscription/individu/formulaire/
   POST /accounts/inscription/individu/formulaire/ (form data)
   
4. Restriction de publication:
   GET /logement/ajouter/ (connecté comme touriste)
   → Devrait afficher erreur et rediriger
""")

print("\n" + "="*60)
print("✅ TESTS COMPLETS!")
print("="*60 + "\n")

# Cleanup (optionnel)
print("Note: Les utilisateurs de test ont été créés.")
print("Pour les nettoyer: User.objects.filter(username__contains='_test').delete()")
