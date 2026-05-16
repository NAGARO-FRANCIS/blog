#!/usr/bin/env python
"""
Final test to verify photo upload in property publication
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

def create_test_image(name='test.jpg'):
    """Create a simple test image"""
    image = Image.new('RGB', (100, 100), color='red')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )

def test_hotel_property():
    """Test hotel property publication with photos"""
    print("\n" + "="*60)
    print("TEST: HOTEL PROPERTY WITH PHOTOS")
    print("="*60)
    
    client = Client()
    try:
        user_hotel = User.objects.get(username='hotel_test')
    except User.DoesNotExist:
        print("❌ User hotel_test not found")
        return False
    
    client.force_login(user_hotel)
    
    # Prepare form data
    form_data = {
        'titre': 'Suite Hôtel Test',
        'description': 'Test publication',
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
        # Formset management
        'photos-TOTAL_FORMS': '3',
        'photos-INITIAL_FORMS': '0',
        'photos-MIN_NUM_FORMS': '0',
        'photos-MAX_NUM_FORMS': '1000',
        'photos-0-image': create_test_image('hotel_photo1.jpg'),
        'photos-0-alt_text': 'Photo 1',
        'photos-0-order': '0',
        'photos-1-image': create_test_image('hotel_photo2.jpg'),
        'photos-1-alt_text': 'Photo 2',
        'photos-1-order': '1',
        'photos-2-image': create_test_image('hotel_photo3.jpg'),
        'photos-2-alt_text': 'Photo 3',
        'photos-2-order': '2',
    }
    
    # Make POST request
    response = client.post(
        reverse('logement:ajouter_logement'),
        data=form_data,
        follow=False
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Form submitted (redirect)")
        
        # Verify property was created
        props = Logement.objects.filter(
            proprietaire=user_hotel,
            titre__contains='Suite Hôtel Test'
        ).order_by('-id')
        
        if props.exists():
            prop = props.first()
            photos = prop.photos.all()
            
            print(f"✅ Property created: {prop.titre}")
            print(f"   Photos uploaded: {photos.count()}")
            
            for photo in photos:
                print(f"   - {photo.image.name}")
            
            return photos.count() >= 3
        else:
            print("❌ Property not created in database")
            return False
    else:
        print(f"❌ Form submission failed (status {response.status_code})")
        return False

def test_residence_property():
    """Test residence property publication with photos"""
    print("\n" + "="*60)
    print("TEST: RESIDENCE PROPERTY WITH PHOTOS")
    print("="*60)
    
    client = Client()
    try:
        user_res = User.objects.get(username='residence_test')
    except User.DoesNotExist:
        print("❌ User residence_test not found")
        return False
    
    client.force_login(user_res)
    
    # Prepare form data
    form_data = {
        'titre': 'T2 Résidence Test',
        'description': 'Test publication',
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
        # Formset management
        'photos-TOTAL_FORMS': '4',
        'photos-INITIAL_FORMS': '0',
        'photos-MIN_NUM_FORMS': '0',
        'photos-MAX_NUM_FORMS': '1000',
        'photos-0-image': create_test_image('res_photo1.jpg'),
        'photos-0-alt_text': 'Salon',
        'photos-0-order': '0',
        'photos-1-image': create_test_image('res_photo2.jpg'),
        'photos-1-alt_text': 'Chambre',
        'photos-1-order': '1',
        'photos-2-image': create_test_image('res_photo3.jpg'),
        'photos-2-alt_text': 'Cuisine',
        'photos-2-order': '2',
        'photos-3-image': create_test_image('res_photo4.jpg'),
        'photos-3-alt_text': 'Salle de bain',
        'photos-3-order': '3',
    }
    
    # Make POST request
    response = client.post(
        reverse('logement:ajouter_logement'),
        data=form_data,
        follow=False
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Form submitted (redirect)")
        
        # Verify property was created
        props = Logement.objects.filter(
            proprietaire=user_res,
            titre__contains='T2 Résidence Test'
        ).order_by('-id')
        
        if props.exists():
            prop = props.first()
            photos = prop.photos.all()
            
            print(f"✅ Property created: {prop.titre}")
            print(f"   Photos uploaded: {photos.count()}")
            
            for photo in photos:
                print(f"   - {photo.image.name}")
            
            return photos.count() >= 4
        else:
            print("❌ Property not created in database")
            return False
    else:
        print(f"❌ Form submission failed (status {response.status_code})")
        return False

def main():
    """Run all tests"""
    print("\n🧪 TESTING PROPERTY PUBLICATION WITH PHOTOS")
    print("="*60)
    
    results = []
    results.append(("Hotel", test_hotel_property()))
    results.append(("Residence", test_residence_property()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
    
    if all(p for _, p in results):
        print("\n🎉 ALL TESTS PASSED - Photo uploads are working!")
    else:
        print("\n⚠️ Some tests failed")

if __name__ == '__main__':
    main()
