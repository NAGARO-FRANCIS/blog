#!/usr/bin/env python
"""
Test script to verify hotel and residence property publication via forms
Run with: python test_logement_publication.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from logement.models import Logement
from django.core.files.uploadedfile import SimpleUploadedFile

def create_test_image():
    """Create a minimal test image"""
    # Simple red square image in bytes
    image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xf6L\x0eJ\x00\x00\x00\x18IDATx\x9c\xed\xc1\x01\x00\x00\x00\x00@\x80\x90\xff\x7fN\x86\x12\xa3\x00\x00\x00\x00IEND\xaeB`\x82'
    return SimpleUploadedFile("test.png", image_content, content_type="image/png")

def test_hotel_publication():
    """Test hotel property publication through the form"""
    print("\n" + "="*60)
    print("TEST 1: HOTEL PROPERTY PUBLICATION")
    print("="*60)
    
    client = Client()
    user_hotel = User.objects.get(username='hotel_test')
    client.force_login(user_hotel)
    
    # Prepare form data for hotel
    form_data = {
        'titre': 'Suite Presidio - Chambre de Test',
        'description': 'Une belle suite climatisée avec vue sur la ville',
        'prix': '150000',  # Prix par défaut
        'prix_par_nuit': '150000',
        'ville': 'Abidjan',
        'quartier': 'Plateau',
        'type_logement': 'chambre',
        'surface': '45',
        'nombre_pieces': '1',
        'nombre_chambres': '1',
        'nombre_lits': '1',
        'capacite': '2',
        'nombre_salles_bain': '1',
        'etage': '3',
        'frais_nettoyage': '5000',
        'min_sejour': '1',
        'disponible_depuis': '2026-05-15',
        'meuble': False,
        'wifi': True,
        'climatisation': True,
        'television': True,
        'minibar': True,
        'coffre_fort': False,
        'reception_24h': True,
        'restaurant': False,
        'garage': False,
        'jardin': False,
        'piscine': False,
        'cuisine_equipee': False,
        # Formset photos (empty for now)
        'photoLogement_set-TOTAL_FORMS': '5',
        'photoLogement_set-INITIAL_FORMS': '0',
        'photoLogement_set-MIN_NUM_FORMS': '0',
        'photoLogement_set-MAX_NUM_FORMS': '1000',
    }
    
    # Submit POST
    response = client.post(reverse('logement:ajouter_logement'), form_data)
    
    if response.status_code == 302:  # Redirect after successful POST
        print("✅ HOTEL FORM SUBMITTED SUCCESSFULLY")
        print(f"   Redirect location: {response.get('Location', 'N/A')}")
        
        # Verify creation
        hotel_logs = Logement.objects.filter(
            proprietaire=user_hotel,
            account_type='hotel',
            titre__contains='Suite Presidio'
        ).order_by('-id')
        
        if hotel_logs.exists():
            latest = hotel_logs.first()
            print(f"   ✅ Property created: {latest.titre} (ID: {latest.id})")
            print(f"      Prix/nuit: {latest.prix_par_nuit} FCFA")
            print(f"      WiFi: {latest.wifi}, Clim: {latest.climatisation}, TV: {latest.television}")
            return True
        else:
            print("   ⚠️  Form redirected but property not found in database")
            return False
    else:
        print(f"❌ HOTEL FORM FAILED - Status {response.status_code}")
        if 'form' in response.context:
            form = response.context['form']
            print(f"   Form errors: {form.errors}")
            print(f"   Form data received: {form.data}")
        return False

def test_residence_publication():
    """Test residence property publication through the form"""
    print("\n" + "="*60)
    print("TEST 2: RESIDENCE PROPERTY PUBLICATION")
    print("="*60)
    
    client = Client()
    user_res = User.objects.get(username='residence_test')
    client.force_login(user_res)
    
    # Prepare form data for residence
    form_data = {
        'titre': 'Bel Appartement T2 Climatisé - Test',
        'description': 'Bel appartement moderne en résidence sécurisée avec parking',
        'prix': '300000',  # Prix par défaut
        'prix_par_mois': '300000',
        'ville': 'Abidjan',
        'quartier': 'Cocody',
        'type_logement': 'appartement',
        'surface': '65',
        'nombre_pieces': '2',
        'nombre_chambres': '1',
        'nombre_lits': '1',
        'capacite': '3',
        'nombre_salles_bain': '1',
        'etage': '2',
        'caution_mois': '2',
        'frais_agence': 'locataire',
        'duree_min_bail': '12',
        'type_charge': 'charges_comprises',
        'conditions_speciales': 'Pas d\'animaux, documents requis',
        'disponible_depuis': '2026-06-01',
        'meuble': False,
        'wifi': True,
        'climatisation': True,
        'cuisine_equipee': True,
        'garage': True,
        'ascenseur': True,
        'gardien': True,
        'securite': False,
        'buanderie': True,
        'jardin': False,
        'piscine': False,
        # Formset photos (empty for now)
        'photoLogement_set-TOTAL_FORMS': '5',
        'photoLogement_set-INITIAL_FORMS': '0',
        'photoLogement_set-MIN_NUM_FORMS': '0',
        'photoLogement_set-MAX_NUM_FORMS': '1000',
    }
    
    # Submit POST
    response = client.post(reverse('logement:ajouter_logement'), form_data)
    
    if response.status_code == 302:  # Redirect after successful POST
        print("✅ RESIDENCE FORM SUBMITTED SUCCESSFULLY")
        print(f"   Redirect location: {response.get('Location', 'N/A')}")
        
        # Verify creation
        res_logs = Logement.objects.filter(
            proprietaire=user_res,
            account_type='residence',
            titre__contains='Bel Appartement'
        ).order_by('-id')
        
        if res_logs.exists():
            latest = res_logs.first()
            print(f"   ✅ Property created: {latest.titre} (ID: {latest.id})")
            print(f"      Loyer/mois: {latest.prix_par_mois} FCFA")
            print(f"      Caution: {latest.caution_mois} mois")
            print(f"      Gardien: {latest.gardien}, Ascenseur: {latest.ascenseur}")
            return True
        else:
            print("   ⚠️  Form redirected but property not found in database")
            return False
    else:
        print(f"❌ RESIDENCE FORM FAILED - Status {response.status_code}")
        if 'form' in response.context:
            form = response.context['form']
            print(f"   Form errors: {form.errors}")
            print(f"   Form data received: {form.data}")
        return False

def main():
    """Run all tests"""
    print("\n🧪 TESTING HOTEL/RESIDENCE PROPERTY PUBLICATION")
    print("="*60)
    
    # Check test users exist
    try:
        User.objects.get(username='hotel_test')
        User.objects.get(username='residence_test')
        print("✅ Test users found")
    except User.DoesNotExist as e:
        print(f"❌ Test users not found: {e}")
        return
    
    # Run tests
    test_results = []
    test_results.append(("Hotel Publication", test_hotel_publication()))
    test_results.append(("Residence Publication", test_residence_publication()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in test_results)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed - check error messages above")

if __name__ == '__main__':
    main()
