#!/usr/bin/env python
"""
Debug: Show actual HTML content around photo section
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

client = Client()

try:
    user = User.objects.get(username='hotel_test')
    client.force_login(user)
except User.DoesNotExist:
    print("❌ User not found")
    exit(1)

response = client.get(reverse('logement:ajouter_logement'))

if response.status_code == 200:
    content = response.content.decode('utf-8')
    
    # Find the photo section
    photo_start = content.find('photo-upload-section')
    if photo_start != -1:
        # Get 500 characters around the photo section
        section_start = max(0, photo_start - 100)
        section_end = min(len(content), photo_start + 1500)
        
        print("="*60)
        print("PHOTO SECTION HTML:")
        print("="*60)
        print(content[section_start:section_end])
        print("="*60)
    else:
        print("❌ Photo section not found in HTML")
    
    # Check for formset data
    if 'photos-TOTAL_FORMS' in content:
        print("\n✅ Found: photos-TOTAL_FORMS field")
        # Find the value
        total_forms_pos = content.find('photos-TOTAL_FORMS')
        print(content[total_forms_pos:total_forms_pos+200])
    
    # Check for photo forms
    photo_item_count = content.count('photo-form-item')
    print(f"\n✅ Found {photo_item_count} photo-form-item elements")
    
    # Check for button
    if 'add-photo-form' in content:
        print("✅ Found: add-photo-form button")
        button_pos = content.find('add-photo-form')
        print(content[button_pos-100:button_pos+200])
    else:
        print("❌ NOT found: add-photo-form button")
    
    # Check for JavaScript
    if 'function addPhotoForm()' in content:
        print("✅ Found: addPhotoForm JavaScript function")
    else:
        print("❌ NOT found: addPhotoForm JavaScript function")
else:
    print(f"❌ Page failed to load (status {response.status_code})")
