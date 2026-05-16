#!/usr/bin/env python
"""
Test script to verify photo upload in property publication forms
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from logement.models import Logement, PhotoLogement
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

def create_test_image(name='test.jpg', size=(100, 100)):
    """Create a simple test image"""
    image = Image.new('RGB', size, color='red')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )

def test_hotel_property_with_photos():
    """Test hotel property publication with photos"""
    print("\n" + "="*60)
    print("TEST: HOTEL PROPERTY WITH PHOTOS")
    print("="*60)
    
    client = Client()
    user_hotel = User.objects.get(username='hotel_test')
    client.force_login(user_hotel)
    
    # Prepare form data
    form_data = {
        'titre': 'Suite Hôtel avec Photos Test',
        'description': 'Test d\'upload de photos',
        'prix': '100000',
        'prix_par_nuit': '100000',
        'ville': 'Abidjan',
        'quartier': 'Plateau',
        'type_logement': 'chambre',
        'surface': '40',
        'nombre_pieces': '1',
        'nombre_chambres': '1',
        'nombre_lits': '1',
        'capacite': '2',
        'nombre_salles_bain': '1',
        'etage': '2',
        'frais_nettoyage': '5000',
        'min_sejour': '1',
        'meuble': False,
        'wifi': True,
        'climatisation': True,
        'television': True,
        'minibar': False,
        'coffre_fort': False,
        'reception_24h': False,
        'restaurant': False,
        'garage': False,
        'jardin': False,
        'piscine': False,
        'cuisine_equipee': False,
        'ascenseur': False,
        'gardien': False,
        'buanderie': False,
        # Formset management forms
        'photos-TOTAL_FORMS': '5',
        'photos-INITIAL_FORMS': '0',
        'photos-MIN_NUM_FORMS': '0',
        'photos-MAX_NUM_FORMS': '1000',
    }
    
    # Add photos to the formset
    files_dict = {
        'photos-0-image': create_test_image('photo1.jpg'),
        'photos-1-image': create_test_image('photo2.jpg'),
        'photos-2-image': create_test_image('photo3.jpg'),
    }
    
    # Add alt text for photos
    form_data.update({
        'photos-0-alt_text': 'Vue générale de la suite',
        'photos-1-alt_text': 'Salle de bain',
        'photos-2-alt_text': 'Lit king size',
        'photos-0-order': '0',
        'photos-1-order': '1',
        'photos-2-order': '2',
        'photos-3-order': '',
        'photos-4-order': '',
        'photos-3-image': '',
        'photos-4-image': '',
    })
    
    # Submit POST request (merge files into form_data for Django test client)
    all_data = form_data.copy()
    all_data.update(files_dict)
    
    response = client.post(
        reverse('logement:ajouter_logement'),
        data=all_data,
        follow=False
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ FORM SUBMITTED (redirect)")
        
        # Verify property and photos were created
        hotel_logs = Logement.objects.filter(
            proprietaire=user_hotel,
            titre__contains='Suite Hôtel avec Photos Test'
        ).order_by('-id')
        
        if hotel_logs.exists():
            logement = hotel_logs.first()
            photos = logement.photos.all()
            
            print(f"✅ Property created: {logement.titre} (ID: {logement.id})")
            print(f"   Photos uploaded: {photos.count()}")
            
            for photo in photos:
                print(f"   - Photo {photo.order+1}: {photo.image.name} (Alt: {photo.alt_text})")
            
            if photos.count() >= 3:
                print(f"✅ SUCCESS: All 3 photos were uploaded")
                return True
            else:
                print(f"⚠️ WARNING: Only {photos.count()} photos uploaded")
                return False
        else:
            print("❌ Property not found in database")
            return False
    else:
        print(f"❌ FORM FAILED - Status {response.status_code}")
        if 'form' in response.context:
            print(f"Form errors: {response.context['form'].errors}")
        if 'formset' in response.context:
            print(f"Formset errors: {response.context['formset'].errors}")
        return False

def test_residence_property_with_photos():
    """Test residence property publication with photos"""
    print("\n" + "="*60)
    print("TEST: RESIDENCE PROPERTY WITH PHOTOS")
    print("="*60)
    
    client = Client()
    user_res = User.objects.get(username='residence_test')
    client.force_login(user_res)
    
    # Prepare form data
    form_data = {
        'titre': 'T2 Résidence avec Photos Test',
        'description': 'Test d\'upload de photos résidence',
        'prix': '250000',
        'prix_par_mois': '250000',
        'ville': 'Abidjan',
        'quartier': 'Cocody',
        'type_logement': 'appartement',
        'surface': '60',
        'nombre_pieces': '2',
        'nombre_chambres': '1',
        'nombre_lits': '1',
        'capacite': '3',
        'nombre_salles_bain': '1',
        'etage': '1',
        'caution_mois': '2',
        'duree_min_bail': '12',
        'type_charge': 'charges_comprises',
        'meuble': False,
        'conditions_speciales': 'Test',
        'wifi': True,
        'climatisation': True,
        'cuisine_equipee': True,
        'garage': True,
        'jardin': False,
        'piscine': False,
        'ascenseur': False,
        'gardien': False,
        'buanderie': False,
        'television': False,
        'minibar': False,
        'coffre_fort': False,
        'reception_24h': False,
        'restaurant': False,
        # Formset management forms
        'photos-TOTAL_FORMS': '5',
        'photos-INITIAL_FORMS': '0',
        'photos-MIN_NUM_FORMS': '0',
        'photos-MAX_NUM_FORMS': '1000',
    }
    
    # Add photos to the formset
    files_dict = {
        'photos-0-image': create_test_image('salon.jpg'),
        'photos-1-image': create_test_image('chambre.jpg'),
        'photos-2-image': create_test_image('cuisine.jpg'),
        'photos-3-image': create_test_image('sdb.jpg'),
    }
    
    # Add alt text for photos
    form_data.update({
        'photos-0-alt_text': 'Salon',
        'photos-1-alt_text': 'Chambre',
        'photos-2-alt_text': 'Cuisine',
        'photos-3-alt_text': 'Salle de bain',
        'photos-0-order': '0',
        'photos-1-order': '1',
        'photos-2-order': '2',
        'photos-3-order': '3',
        'photos-4-order': '',
        'photos-4-image': '',
    })
    
    # Submit POST request (merge files into form_data for Django test client)
    all_data = form_data.copy()
    all_data.update(files_dict)
    
    response = client.post(
        reverse('logement:ajouter_logement'),
        data=all_data,
        follow=False
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ FORM SUBMITTED (redirect)")
        
        # Verify property and photos were created
        res_logs = Logement.objects.filter(
            proprietaire=user_res,
            titre__contains='T2 Résidence avec Photos Test'
        ).order_by('-id')
        
        if res_logs.exists():
            logement = res_logs.first()
            photos = logement.photos.all()
            
            print(f"✅ Property created: {logement.titre} (ID: {logement.id})")
            print(f"   Photos uploaded: {photos.count()}")
            
            for photo in photos:
                print(f"   - Photo {photo.order+1}: {photo.image.name} (Alt: {photo.alt_text})")
            
            if photos.count() >= 4:
                print(f"✅ SUCCESS: All 4 photos were uploaded")
                return True
            else:
                print(f"⚠️ WARNING: Only {photos.count()} photos uploaded")
                return False
        else:
            print("❌ Property not found in database")
            return False
    else:
        print(f"❌ FORM FAILED - Status {response.status_code}")
        if 'form' in response.context:
            print(f"Form errors: {response.context['form'].errors}")
        if 'formset' in response.context:
            print(f"Formset errors: {response.context['formset'].errors}")
        return False

def main():
    """Run all tests"""
    print("\n🧪 TESTING PHOTO UPLOAD IN PROPERTY PUBLICATION")
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
    test_results.append(("Hotel Photos Upload", test_hotel_property_with_photos()))
    test_results.append(("Residence Photos Upload", test_residence_property_with_photos()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in test_results)
    if all_passed:
        print("\n🎉 ALL PHOTO UPLOAD TESTS PASSED!")
    else:
        print("\n⚠️ Some tests failed - check error messages above")

if __name__ == '__main__':
    main()
