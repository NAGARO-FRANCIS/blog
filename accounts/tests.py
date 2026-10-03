import io
import importlib
import os
from smtplib import SMTPException
import tempfile
from unittest import mock

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import DocumentVerification, Notification, ProfileVerification, Subscription
from .notification_service import notify_user


class PublicLanguageSelectionTests(TestCase):
    def test_anonymous_visitor_can_select_english_from_the_public_header(self):
        response = self.client.get(reverse('accounts:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="language-select"')
        self.assertContains(response, '<option value="en"')

    def test_anonymous_visitor_language_change_returns_to_current_page(self):
        response = self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('accounts:login')},
        )

        self.assertRedirects(response, reverse('accounts:login'))
        self.assertEqual(response.cookies['django_language'].value, 'en')


class AccountActivationTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_individual_signup_creates_inactive_user_and_sends_activation_email(self):
        session = self.client.session
        session['account_type'] = 'individu'
        session['individu_role'] = 'touriste'
        session.save()

        response = self.client.post(reverse('accounts:inscription_individu_form'), {
            'first_name': 'Nagaro',
            'last_name': 'Touriste',
            'email': 'nagaro@example.com',
            'username': 'nagaro_touriste',
            'telephone': '+22501020304',
            'ville': 'Abidjan',
            'quartier': 'Plateaux',
            'date_naissance': '1990-01-01',
            'sexe': 'M',
            'profession': 'Développeur',
            'type_piece_identite': 'cni',
            'numero_piece_identite': 'CI123456789',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('activation', mail.outbox[0].subject.lower())

    def test_smtp_backend_is_used_when_smtp_env_is_configured(self):
        with mock.patch.dict(os.environ, {
            'EMAIL_BACKEND': '',
            'EMAIL_HOST': 'smtp.gmail.com',
            'EMAIL_HOST_USER': 'user@example.com',
            'EMAIL_HOST_PASSWORD': ' abcd efgh ijkl mnop ',
            'EMAIL_PORT': '587',
            'EMAIL_USE_TLS': 'True',
            'DEFAULT_FROM_EMAIL': 'user@example.com',
        }, clear=False):
            settings_module = importlib.import_module('ivoire.settings')
            reloaded_settings = importlib.reload(settings_module)

        self.assertEqual(
            reloaded_settings.EMAIL_BACKEND,
            'django.core.mail.backends.smtp.EmailBackend'
        )
        self.assertEqual(reloaded_settings.EMAIL_HOST_PASSWORD, 'abcdefghijklmnop')

    def test_notification_smtp_errors_are_not_silenced(self):
        recipient = User.objects.create_user(
            username='email_error_test',
            email='email.error@example.com',
            password='StrongPassword123!',
        )

        with mock.patch(
            'accounts.notification_service.send_mail',
            side_effect=SMTPException('SMTP authentication failed'),
        ):
            with self.assertRaises(SMTPException):
                notify_user(
                    recipient,
                    'system',
                    'Test',
                    'Test message',
                    email_subject='Test email',
                )

    def test_password_reset_done_page_shows_resend_button_after_submit(self):
        user = User.objects.create_user(
            username='reset_test',
            email='reset.test@example.com',
            password='StrongPassword123!'
        )

        response = self.client.post(reverse('accounts:password_reset'), {'email': user.email}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['password_reset_email'], user.email)
        self.assertContains(response, 'Recevoir un nouveau lien')

    def test_profile_page_renders_with_verification_state(self):
        viewer = User.objects.create_user(
            username='viewer_test',
            email='viewer.test@example.com',
            password='StrongPassword123!'
        )
        target_user = User.objects.create_user(
            username='target_test',
            email='target.test@example.com',
            password='StrongPassword123!'
        )

        ProfileVerification.objects.create(verifier=viewer, verified_profile=target_user.profile)

        self.client.force_login(viewer)
        response = self.client.get(reverse('accounts:profil'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'vérification')

    def test_profile_page_for_other_user_shows_follow_button(self):
        owner = User.objects.create_user(
            username='owner_follow_test',
            email='owner.follow@example.com',
            password='StrongPassword123!'
        )
        viewer = User.objects.create_user(
            username='viewer_follow_test',
            email='viewer.follow@example.com',
            password='StrongPassword123!'
        )

        self.client.force_login(viewer)
        response = self.client.get(reverse('accounts:profil_user', args=[owner.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suivre ce profil')
        self.assertContains(response, 'Recevez ses nouvelles annonces')

    def test_subscribe_creates_subscription_and_notification(self):
        creator = User.objects.create_user(
            username='creator_test',
            email='creator.test@example.com',
            password='StrongPassword123!'
        )
        subscriber = User.objects.create_user(
            username='subscriber_test',
            email='subscriber.test@example.com',
            password='StrongPassword123!'
        )

        self.client.force_login(subscriber)
        response = self.client.post(reverse('accounts:subscribe', args=[creator.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscription.objects.filter(subscriber=subscriber, creator=creator, is_active=True).exists())
        self.assertTrue(Notification.objects.filter(recipient=creator, notification_type='subscription').exists())

    def test_mark_notification_as_read_updates_state(self):
        recipient = User.objects.create_user(
            username='reader_test',
            email='reader.test@example.com',
            password='StrongPassword123!'
        )
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type='system',
            title='Test',
            message='Bonjour'
        )

        self.client.force_login(recipient)
        response = self.client.post(reverse('accounts:mark_notification_as_read', args=[notification.id]))

        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_authentication_activates_pending_account_with_valid_credentials(self):
        user = User.objects.create_user(
            username='thales_test',
            email='thales.test@example.com',
            password='StrongPassword123!'
        )
        user.is_active = False
        user.save(update_fields=['is_active'])

        profile = user.profile
        profile.activation_token = 'pending-token'
        profile.activation_token_created_at = timezone.now()
        profile.save(update_fields=['activation_token', 'activation_token_created_at'])

        authenticated_user = authenticate(username='thales_test', password='StrongPassword123!')

        self.assertIsNotNone(authenticated_user)
        self.assertTrue(authenticated_user.is_active)
        authenticated_user.refresh_from_db()
        self.assertTrue(authenticated_user.is_active)


class DocumentUploadSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='document_upload_test',
            password='StrongPassword123!',
        )
        self.client.force_login(self.user)

    def make_image_upload(self, name='identity.jpg', color=(20, 80, 140)):
        image_bytes = io.BytesIO()
        Image.new('RGB', (10, 10), color=color).save(image_bytes, format='JPEG')
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type='image/jpeg')

    def test_forged_image_content_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse('accounts:upload_document'),
                {
                    'document_type': 'id_front',
                    'document_file': SimpleUploadedFile(
                        'fake.jpg',
                        b'not an image',
                        content_type='image/jpeg',
                    ),
                },
            )

        self.assertRedirects(response, reverse('accounts:verification_docs'))
        self.assertFalse(DocumentVerification.objects.filter(profile=self.user.profile).exists())
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.verified)

    def test_uploaded_documents_remain_pending_until_reviewed(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            for index, document_type in enumerate(('id_front', 'id_back', 'selfie')):
                response = self.client.post(
                    reverse('accounts:upload_document'),
                    {
                        'document_type': document_type,
                        'document_file': self.make_image_upload(
                            f'{document_type}.jpg',
                            color=(20 + index, 80, 140),
                        ),
                    },
                )
                self.assertRedirects(response, reverse('accounts:verification_docs'))

        self.assertEqual(
            DocumentVerification.objects.filter(profile=self.user.profile, status='pending').count(),
            3,
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.verification_status, 'pending')
        self.assertFalse(self.user.profile.verified)
