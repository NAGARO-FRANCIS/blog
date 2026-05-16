#!/usr/bin/env python
"""
Simple test to debug photo upload issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from logement.forms import LogementForm, PhotoLogementFormSet
from logement.models import PhotoLogement
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

print("\n" + "="*60)
print("DEBUG: Testing Form Validation with Photos")
print("="*60)

# Test 1: Validate formset with photos
print("\nTest 1: PhotoLogementFormSet with Image")
print("-" * 40)

formset_data = {
    'photos-TOTAL_FORMS': '2',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    'photos-0-image': create_test_image('photo1.jpg'),
    'photos-0-alt_text': 'Test photo 1',
    'photos-0-order': '0',
    'photos-1-image': '',
    'photos-1-alt_text': '',
    'photos-1-order': '',
}

formset = PhotoLogementFormSet(
    data=formset_data,
    files=formset_data
)
    print("✅ Formset is VALID")
    print(f"   Forms with data: {sum(1 for form in formset if form.cleaned_data)}")
else:
    print("❌ Formset has errors:")
    for i, form in enumerate(formset):
        if form.errors:
            print(f"   Form {i}: {form.errors}")

# Test 2: Validate LogementForm
print("\nTest 2: LogementForm without photos")
print("-" * 40)

form_data = {
    'titre': 'Test Property',
    'description': 'Test description',
    'prix': '100000',
    'prix_par_nuit': '100000',
    'ville': 'Abidjan',
    'quartier': 'Test',
    'type_logement': 'chambre',
    'surface': '30',
    'nombre_pieces': '1',
    'nombre_chambres': '1',
    'nombre_lits': '1',
    'capacite': '2',
    'nombre_salles_bain': '1',
    'etage': '1',
    'meuble': False,
    'wifi': True,
    'climatisation': True,
    'television': False,
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
}

form = LogementForm(data=form_data)
if form.is_valid():
    print("✅ Form is VALID")
else:
    print("❌ Form has errors:")
    for field, errors in form.errors.items():
        print(f"   {field}: {errors}")

# Test 3: Client test with simple POST
print("\nTest 3: Client POST Request")
print("-" * 40)

client = Client()
try:
    user = User.objects.get(username='hotel_test')
    client.force_login(user)
    print(f"✅ Logged in as: {user.username}")
    
    # Prepare form data
    form_data = {
        'titre': 'Client Test Property',
        'description': 'Test via client',
        'prix': '50000',
        'prix_par_nuit': '50000',
        'ville': 'Abidjan',
        'quartier': 'Test',
        'type_logement': 'chambre',
        'surface': '25',
        'nombre_pieces': '1',
        'nombre_chambres': '1',
        'nombre_lits': '1',
        'capacite': '2',
        'nombre_salles_bain': '1',
        'etage': '1',
        'meuble': False,
        'wifi': True,
        'climatisation': True,
        'television': False,
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
        'photos-TOTAL_FORMS': '1',
        'photos-INITIAL_FORMS': '0',
        'photos-MIN_NUM_FORMS': '0',
        'photos-MAX_NUM_FORMS': '1000',
        'photos-0-image': create_test_image('test.jpg'),
        'photos-0-alt_text': 'Test',
        'photos-0-order': '0',
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
