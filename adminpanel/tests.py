from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import DocumentVerification, Notification, Profile


class AdminPanelDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.profile = Profile.objects.get(user=self.admin)
        self.profile.verification_status = 'pending'
        self.profile.save(update_fields=['verification_status'])

        DocumentVerification.objects.create(
            profile=self.profile,
            document_type='id_front',
            document_file=SimpleUploadedFile('front.jpg', b'fake-image', content_type='image/jpeg'),
            status='pending',
        )

        Notification.objects.create(
            recipient=self.admin,
            notification_type='system',
            title='Nouvelle alerte admin',
            message='Des vérifications sont en attente.',
        )

    def test_dashboard_exposes_recent_notifications_and_pending_items(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('adminpanel:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('recent_notifications', response.context)
        self.assertEqual(len(response.context['recent_notifications']), 1)
        self.assertEqual(response.context['documents_en_attente'], 1)

    def test_notifications_section_displays_alerts(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('adminpanel:notifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouvelle alerte admin')
