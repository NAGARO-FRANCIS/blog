#!/usr/bin/env python
"""Script pour tester la redirection des dashboards"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

print("\n" + "="*70)
print("TEST DES REDIRECTIONS DES DASHBOARDS")
print("="*70 + "\n")

# Créer un client de test
client = Client()

# Tester avec Louise (residence)
print("1️⃣ TEST AVEC LOUISE (RESIDENCE)")
print("-" * 70)

louise = User.objects.get(username='Louise')
print(f"👤 Utilisateur: {louise.username}")
print(f"   Type de compte: {louise.profile.account_type}")

# Essayer de se connecter et accéder au dashboard
if client.login(username='Louise', password='louise123'):
    print("✅ Connexion réussie")
    
    # Tester l'accès au dashboard router
    response = client.get('/accounts/dashboard/')
    print(f"\n📍 GET /accounts/dashboard/")
    print(f"   Status code: {response.status_code}")
    print(f"   URL finale: {response.url if hasattr(response, 'url') else 'redirection'}")
    
    # Tester l'accès direct au dashboard residence
    response = client.get('/accounts/dashboard/residence/')
    print(f"\n📍 GET /accounts/dashboard/residence/")
    print(f"   Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Dashboard Résidence accessible")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    client.logout()
else:
    print("❌ Connexion échouée")

# Chercher un utilisateur individu
print("\n\n2️⃣ TEST AVEC UN UTILISATEUR INDIVIDU")
print("-" * 70)

individu = User.objects.filter(profile__account_type='individu').first()
if individu:
    print(f"👤 Utilisateur: {individu.username}")
    print(f"   Type de compte: {individu.profile.account_type}")
    
    # Essayer d'accéder au dashboard
    response = client.get('/accounts/dashboard/')
    print(f"\n📍 GET /accounts/dashboard/ (avant connexion)")
    print(f"   Status code: {response.status_code}")
    print(f"   Redirect: {response.status_code == 302}")

print("\n" + "="*70)
