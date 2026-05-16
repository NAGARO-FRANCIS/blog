#!/usr/bin/env python
"""
Test to verify the add photo button functionality in browser
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

print("\n" + "="*60)
print("TEST: Accessing property publication form")
print("="*60 + "\n")

client = Client()

# Try to login as hotel_test user
try:
    user = User.objects.get(username='hotel_test')
    client.force_login(user)
    print(f"✅ Logged in as: {user.username}")
except User.DoesNotExist:
    print("❌ User not found")
    exit(1)

# Get the property publication form
response = client.get(reverse('logement:ajouter_logement'))

print(f"Response status: {response.status_code}")

if response.status_code == 200:
    print("✅ Form page loaded successfully")
    
    # Check for required elements
    content = response.content.decode('utf-8')
    
    checks = [
        ('add-photo-form button', 'id="add-photo-form"' in content),
        ('photos-TOTAL_FORMS field', 'name="photos-TOTAL_FORMS"' in content),
        ('photo-forms-container', 'id="photo-forms-container"' in content),
        ('JavaScript function addPhotoForm', 'function addPhotoForm()' in content),
        ('JavaScript function updateFormIndices', 'function updateFormIndices' in content),
        ('first photo form', 'class="photo-form-item"' in content),
    ]
    
    print("\nRequired elements check:")
    for name, found in checks:
        status = "✅" if found else "❌"
        print(f"  {status} {name}")
    
    if all(found for _, found in checks):
        print("\n✅ All required elements are present!")
        print("\nThe add-photo button should now work. You can:")
        print("  1. Load the property form in your browser")
        print("  2. Go to the Photos step (step 5)")
        print("  3. Click '+ Ajouter une autre photo' button")
        print("  4. A new photo form should appear below")
    else:
        print("\n❌ Some elements are missing!")
else:
    print(f"❌ Form page failed to load (status {response.status_code})")

print("\n" + "="*60)
