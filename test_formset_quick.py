#!/usr/bin/env python
"""
Quick test to verify photo upload formset works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from logement.forms import PhotoLogementFormSet
from logement.models import PhotoLogement, Logement
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

def create_test_image(name='test.jpg'):
    """Create a test image"""
    img = Image.new('RGB', (10, 10), color='red')
    f = BytesIO()
    img.save(f, 'JPEG')
    f.seek(0)
    return SimpleUploadedFile(name, f.getvalue(), content_type='image/jpeg')

print("Testing PhotoLogementFormSet with empty and filled forms...\n")

# Get or create a test logement
user = User.objects.first() or User.objects.create_user('testuser', 'test@test.com', '123456')
logement = Logement.objects.create(
    titre='Test Property',
    description='Test',
    prix=100,
    ville='Test',
    proprietaire=user
)

# Test with 3 photos (forms 0, 1, 2) and 2 empty forms (forms 3, 4)
files_dict = {
    'photos-0-image': create_test_image('photo1.jpg'),
    'photos-1-image': create_test_image('photo2.jpg'),
    'photos-2-image': create_test_image('photo3.jpg'),
}

data = {
    'photos-TOTAL_FORMS': '5',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    # Photo 1
    'photos-0-image': files_dict['photos-0-image'],
    'photos-0-alt_text': 'Photo 1',
    'photos-0-order': '0',
    # Photo 2
    'photos-1-image': files_dict['photos-1-image'],
    'photos-1-alt_text': 'Photo 2',
    'photos-1-order': '1',
    # Photo 3
    'photos-2-image': files_dict['photos-2-image'],
    'photos-2-alt_text': 'Photo 3',
    'photos-2-order': '2',
    # Empty forms
    'photos-3-image': '',
    'photos-3-alt_text': '',
    'photos-3-order': '',
    'photos-4-image': '',
    'photos-4-alt_text': '',
    'photos-4-order': '',
}

formset = PhotoLogementFormSet(data=data, files=files_dict, instance=logement)

print(f"Formset is valid: {formset.is_valid()}")

if not formset.is_valid():
    print("❌ ERRORS:")
    print(f"  Non-form errors: {formset.non_form_errors()}")
    for i, form in enumerate(formset):
        if form.errors:
            print(f"  Form {i}: {form.errors}")
else:
    print("✅ FORMSET VALID!")
    
    # Debug: check what's in the forms
    print("\nDebug: Checking formset forms:")
    for i, form_photo in enumerate(formset):
        if form_photo.cleaned_data:
            image = form_photo.cleaned_data.get('image')
            print(f"  Form {i}: image={image}, has_image={bool(image)}")
        else:
            print(f"  Form {i}: No cleaned_data")
    
    # Save the formset - only save non-empty forms
    try:
        count = 0
        for i, form_photo in enumerate(formset):
            if form_photo.cleaned_data and form_photo.cleaned_data.get('image'):
                form_photo.save()
                count += 1
                print(f"  Saved photo from form {i}")
        
        print(f"✅ Saved {count} photos")
        
        photos = logement.photos.all()
        print(f"Total photos in logement: {photos.count()}")
        
        for photo in photos:
            print(f"  - {photo.image.name} (Order: {photo.order})")
    except Exception as e:
        print(f"❌ Error saving: {e}")

# Cleanup
logement.delete()
print("\n✅ Test completed")
