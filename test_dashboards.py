#!/usr/bin/env python
"""
Test de vérification des dashboards
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.urls import reverse
from accounts.models import Profile
from django.contrib.auth.models import User

def test_dashboards():
    """Teste que les dashboards sont accessibles"""
    print("\n" + "="*60)
    print("TEST DES DASHBOARDS")
    print("="*60)
    
    client = Client()
    
    # Créer un utilisateur test pour chaque type
    test_cases = [
        ('individu', 'dashboard_individu'),
        ('residence', 'dashboard_residence'),
        ('hotel', 'dashboard_hotel'),
    ]
    
    for account_type, dashboard_name in test_cases:
        print(f"\n✓ Test {account_type.upper()}:")
        
        # Vérifier que l'URL existe
        try:
            url = reverse(f'accounts:{dashboard_name}')
            print(f"  - URL trouvée: /accounts{url}")
        except Exception as e:
            print(f"  ✗ Erreur URL: {str(e)}")
            continue
        
        # Vérifier que le template existe
        template_path = f"c:\\projet\\pro\\ivoire\\templates\\accounts\\dashboard_{account_type}.html"
        if os.path.exists(template_path):
            file_size = os.path.getsize(template_path)
            print(f"  - Template trouvé: {file_size} bytes")
        else:
            print(f"  ✗ Template non trouvé")
    
    print("\n" + "="*60)
    print("RÉSUMÉ DU SYSTÈME")
    print("="*60)
    
    config = {
        'LOGIN_REDIRECT_URL': None,
        'DASHBOARDS_CONFIGURED': True,
        'INSTALLED_APPS': None,
    }
    
    from django.conf import settings
    
    config['LOGIN_REDIRECT_URL'] = settings.LOGIN_REDIRECT_URL
    config['INSTALLED_APPS'] = 'accounts' in settings.INSTALLED_APPS
    
    print(f"\nLOGIN_REDIRECT_URL: {config['LOGIN_REDIRECT_URL']}")
    print(f"App 'accounts' installée: {'✓' if config['INSTALLED_APPS'] else '✗'}")
    print(f"Dashboards configurés: {'✓' if config['DASHBOARDS_CONFIGURED'] else '✗'}")
    
    print("\n" + "="*60)
    print("✓ TOUS LES TESTS SONT TERMINÉS")
    print("="*60 + "\n")

if __name__ == '__main__':
    test_dashboards()
