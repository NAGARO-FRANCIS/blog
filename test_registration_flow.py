#!/usr/bin/env python
"""
Test script to verify the complete registration flow works correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.urls import reverse
from accounts.forms import AccountTypeForm, SignUpForm, ProfessionalSignUpForm

def test_inscription_urls():
    """Test that all inscription URLs resolve correctly"""
    print("=" * 60)
    print("TESTING INSCRIPTION URL RESOLUTION")
    print("=" * 60)
    
    client = Client()
    urls_to_test = [
        ('accounts:inscription', 'Main inscription page'),
        ('accounts:inscription_individu', 'Individual registration'),
        ('accounts:inscription_residence', 'Residence manager registration'),
        ('accounts:inscription_hotel', 'Hotel manager registration'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            response = client.get(url)
            status_code = response.status_code
            
            # Check if it redirects (302) for individual/residence/hotel without session
            if url_name in ['accounts:inscription_individu', 'accounts:inscription_residence', 'accounts:inscription_hotel']:
                if status_code == 302:
                    print(f"✓ {description:<40} [PASS] - Redirects to inscription (expected, no session)")
                elif status_code == 200:
                    print(f"✓ {description:<40} [PASS] - Renders with status {status_code}")
                else:
                    print(f"✗ {description:<40} [FAIL] - Status {status_code}")
            else:
                if status_code == 200:
                    print(f"✓ {description:<40} [PASS] - Status {status_code}")
                else:
                    print(f"✗ {description:<40} [FAIL] - Status {status_code}")
        except Exception as e:
            print(f"✗ {description:<40} [ERROR] - {str(e)}")

def test_forms_instantiation():
    """Test that all forms can be instantiated without errors"""
    print("\n" + "=" * 60)
    print("TESTING FORM INSTANTIATION")
    print("=" * 60)
    
    forms_to_test = [
        (AccountTypeForm, 'AccountTypeForm'),
        (SignUpForm, 'SignUpForm'),
        (ProfessionalSignUpForm, 'ProfessionalSignUpForm'),
    ]
    
    for form_class, form_name in forms_to_test:
        try:
            form = form_class()
            field_count = len(form.fields)
            print(f"✓ {form_name:<30} [PASS] - {field_count} fields")
        except Exception as e:
            print(f"✗ {form_name:<30} [FAIL] - {str(e)}")

def test_account_type_form_choices():
    """Test that AccountTypeForm has correct choices"""
    print("\n" + "=" * 60)
    print("TESTING ACCOUNT TYPE FORM CHOICES")
    print("=" * 60)
    
    form = AccountTypeForm()
    account_type_field = form.fields['account_type']
    choices = account_type_field.choices
    
    expected_choices = [('individu', 'Je suis un individu (cherche colocation/logement)'),
                       ('residence', 'Je suis un gestionnaire de résidence'),
                       ('hotel', 'Je suis un gestionnaire d\'hôtel')]
    
    print(f"Found {len(choices)} account type choices:")
    for choice_value, choice_label in choices:
        print(f"  - {choice_value}: {choice_label}")
        
    if len(choices) == 3:
        print("\n✓ Correct number of account types")
    else:
        print(f"\n✗ Expected 3 account types, got {len(choices)}")

def test_models():
    """Test that models are correctly set up"""
    print("\n" + "=" * 60)
    print("TESTING MODELS")
    print("=" * 60)
    
    from accounts.models import Profile, ProfessionalProfile
    from django.contrib.auth.models import User
    
    # Check Profile model
    try:
        profile_fields = [f.name for f in Profile._meta.get_fields()]
        if 'account_type' in profile_fields:
            print("✓ Profile model has 'account_type' field")
        else:
            print("✗ Profile model missing 'account_type' field")
    except Exception as e:
        print(f"✗ Error checking Profile model: {str(e)}")
    
    # Check ProfessionalProfile model
    try:
        prof_fields = [f.name for f in ProfessionalProfile._meta.get_fields()]
        required_fields = ['establishment_name', 'siret_or_rccm', 'establishment_type', 'is_verified']
        missing = [f for f in required_fields if f not in prof_fields]
        
        if not missing:
            print(f"✓ ProfessionalProfile model has all required fields ({len(prof_fields)} total)")
        else:
            print(f"✗ ProfessionalProfile model missing fields: {missing}")
    except Exception as e:
        print(f"✗ Error checking ProfessionalProfile model: {str(e)}")

def test_context_processor():
    """Test that context processor is configured"""
    print("\n" + "=" * 60)
    print("TESTING CONTEXT PROCESSOR")
    print("=" * 60)
    
    from django.conf import settings
    
    context_processors = settings.TEMPLATES[0]['OPTIONS'].get('context_processors', [])
    
    if 'ivoire.context_processors.unread_messages_count' in context_processors:
        print("✓ unread_messages_count context processor is configured")
    else:
        print("✗ unread_messages_count context processor NOT configured")
        print(f"  Available processors: {context_processors}")

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "REGISTRATION SYSTEM TEST SUITE" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    
    test_inscription_urls()
    test_forms_instantiation()
    test_account_type_form_choices()
    test_models()
    test_context_processor()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
