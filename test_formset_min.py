#!/usr/bin/env python
"""
Minimal test to find the exact formset error
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

print("\n=== TESTING PHOTOLOGEMENTFORMSET ===\n")

# Get or create a test logement
user = User.objects.first() or User.objects.create_user('testuser', 'test@test.com', '123456')
logement = Logement.objects.create(
    titre='Test Property',
    description='Test',
    prix=100,
    ville='Test',
    proprietaire=user
)

print(f"Test logement created: {logement.id}")

# Test 1: Empty formset
print("\n1. Testing empty formset (no photos):")
data_empty = {
    'photos-TOTAL_FORMS': '1',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    'photos-0-image': '',
    'photos-0-alt_text': '',
    'photos-0-order': '',
}

formset = PhotoLogementFormSet(data_empty, instance=logement)
print(f"   is_valid: {formset.is_valid()}")
if not formset.is_valid():
    print(f"   Errors: {formset.errors}")
    print(f"   Non-form errors: {formset.non_form_errors()}")

# Test 2: Formset with one image
print("\n2. Testing formset with one image:")
files = {
    'photos-0-image': create_test_image('test.jpg'),
}

data_with_photo = {
    'photos-TOTAL_FORMS': '1',
    'photos-INITIAL_FORMS': '0',
    'photos-MIN_NUM_FORMS': '0',
    'photos-MAX_NUM_FORMS': '1000',
    'photos-0-image': files['photos-0-image'],
    'photos-0-alt_text': 'Test',
    'photos-0-order': '0',
}

formset = PhotoLogementFormSet(data_with_photo, files=files, instance=logement)
print(f"   is_valid: {formset.is_valid()}")
if not formset.is_valid():
    print(f"   Errors: {formset.errors}")
    print(f"   Non-form errors: {formset.non_form_errors()}")
    for i, form in enumerate(formset):
        if form.errors:
            print(f"   Form {i} errors: {form.errors}")
else:
    print("   ✅ VALID!")
    for form in formset:
        print(f"      Photo: {form.cleaned_data}")

# Test 3: Try saving the formset
print("\n3. Testing formset save:")
if formset.is_valid():
    try:
        instances = formset.save(commit=True)
        print(f"   ✅ Saved {len(instances)} photo(s)")
        photos = logement.photos.all()
        print(f"   Total photos in logement: {photos.count()}")
        for photo in photos:
            print(f"      - {photo.image.name}")
    except Exception as e:
        print(f"   ❌ Error saving: {e}")
        import traceback
        traceback.print_exc()

# Cleanup
logement.delete()
print("\n✅ Test completed")
