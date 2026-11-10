import io
import importlib
import os
from smtplib import SMTPException
import tempfile
from unittest import mock
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image

from .forms import ProfileEditForm
from .models import (
    DocumentVerification,
    Notification,
    Profile,
    ProfessionalProfile,
    ProfileVerification,
    Subscription,
)
from .notification_service import notify_user
from .views import send_sms


class ProfileEditFormTests(TestCase):
    def test_profile_edit_page_renders_for_authenticated_user(self):
        user = User.objects.create_user(
            username='profile_edit_test',
            email='profile.edit@example.com',
            password='StrongPassword123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:edit_profil'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profile.edit@example.com')

    def test_profile_email_can_remain_unchanged(self):
        user = User.objects.create_user(
            username='profile_email_unchanged',
            email='profile.unchanged@example.com',
            password='StrongPassword123!',
        )

        form = ProfileEditForm(
            data={
                'first_name': 'Test',
                'last_name': 'User',
                'email': user.email,
                'telephone': '+22501020304',
                'ville': 'Abidjan',
                'profession': 'Développeur',
            },
            instance=user.profile,
            user=user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_profile_email_rejects_another_users_email(self):
        user = User.objects.create_user(
            username='profile_email_owner',
            email='profile.owner@example.com',
            password='StrongPassword123!',
        )
        other_user = User.objects.create_user(
            username='profile_email_other',
            email='profile.other@example.com',
            password='StrongPassword123!',
        )

        form = ProfileEditForm(
            data={
                'first_name': 'Test',
                'last_name': 'User',
                'email': other_user.email,
                'telephone': '+22501020304',
                'ville': 'Abidjan',
                'profession': 'Développeur',
            },
            instance=user.profile,
            user=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProfilePersistenceTests(TestCase):
    def test_saving_user_does_not_overwrite_profile_changes_from_a_stale_instance(self):
        user = User.objects.create_user(
            username='profile_persistence_test',
            password='StrongPassword123!',
        )
        stale_profile = user.profile
        current_profile = Profile.objects.get(user=user)
        current_profile.verified = True
        current_profile.verification_status = 'verified'
        current_profile.save(update_fields=['verified', 'verification_status'])

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        current_profile.refresh_from_db()
        self.assertTrue(current_profile.verified)
        self.assertEqual(current_profile.verification_status, 'verified')
        self.assertFalse(stale_profile.verified)


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
    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    @mock.patch('accounts.views.send_sms', return_value=True)
    def test_individual_signup_creates_inactive_user_and_sends_activation_email(self, send_sms_mock):
        administrator = User.objects.create_user(
            username='signup_admin',
            email='admin@example.com',
            password='StrongPassword123!',
            is_staff=True,
        )
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
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('activation', mail.outbox[0].subject.lower())
        self.assertIn('nouvelle inscription', mail.outbox[1].subject.lower())
        notification = Notification.objects.get(
            recipient=administrator,
            notification_type='system',
            title='Nouvelle inscription',
        )
        self.assertIn('Nagaro Touriste', notification.message)
        self.assertIn('Touriste', notification.message)
        self.assertEqual(
            User.objects.get(username='nagaro_touriste').profile.telephone,
            '+22501020304',
        )
        send_sms_mock.assert_called_once()
        self.assertEqual(send_sms_mock.call_args.args[0], '+22501020304')

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    @mock.patch('accounts.views.send_sms', return_value=True)
    def test_professional_signup_sends_code_to_saved_phone(self, send_sms_mock):
        administrator = User.objects.create_user(
            username='professional_signup_admin',
            email='professional-admin@example.com',
            password='StrongPassword123!',
            is_staff=True,
        )
        image_bytes = io.BytesIO()
        Image.new('RGB', (10, 10), (80, 120, 160)).save(image_bytes, format='JPEG')
        session = self.client.session
        session['account_type'] = 'hotel'
        session.save()

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse('accounts:inscription_hotel'),
                {
                    'first_name': 'Gestionnaire',
                    'last_name': 'Test',
                    'email': 'hotel.manager@example.com',
                    'username': 'hotel_manager_test',
                    'telephone': '+2250701020304',
                    'password1': 'StrongPassword123!',
                    'password2': 'StrongPassword123!',
                    'establishment_name': 'Hôtel test',
                    'siret_or_rccm': 'CI-HOTEL-TEST-1',
                    'legal_phone': '+2250705060708',
                    'establishment_address': 'Plateaux',
                    'establishment_city': 'Abidjan',
                    'number_of_rooms': '5',
                    'type_piece_identite': 'cni',
                    'numero_piece_identite': 'CI-HOTEL-ID-1',
                    'legal_document': SimpleUploadedFile(
                        'legal.pdf',
                        b'%PDF-1.4 test document',
                        content_type='application/pdf',
                    ),
                    'establishment_photo': SimpleUploadedFile(
                        'hotel.jpg',
                        image_bytes.getvalue(),
                        content_type='image/jpeg',
                    ),
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            User.objects.get(username='hotel_manager_test').profile.telephone,
            '+2250701020304',
        )
        notification = Notification.objects.get(
            recipient=administrator,
            notification_type='system',
            title='Nouvelle inscription',
        )
        self.assertIn('Hôtel test', notification.message)
        self.assertTrue(any('nouvelle inscription' in message.subject.lower() for message in mail.outbox))
        self.assertEqual(send_sms_mock.call_args.args[0], '+2250701020304')

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    @mock.patch('accounts.views.send_sms', return_value=True)
    def test_residence_signup_notifies_administrator(self, send_sms_mock):
        administrator = User.objects.create_user(
            username='residence_signup_admin',
            email='residence-admin@example.com',
            password='StrongPassword123!',
            is_staff=True,
        )
        image_bytes = io.BytesIO()
        Image.new('RGB', (10, 10), (80, 120, 160)).save(image_bytes, format='JPEG')
        session = self.client.session
        session['account_type'] = 'residence'
        session.save()

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse('accounts:inscription_residence'),
                {
                    'first_name': 'Gestionnaire',
                    'last_name': 'Residence',
                    'email': 'residence.manager@example.com',
                    'username': 'residence_manager_test',
                    'telephone': '+2250701020305',
                    'password1': 'StrongPassword123!',
                    'password2': 'StrongPassword123!',
                    'establishment_name': 'Résidence test',
                    'siret_or_rccm': 'CI-RESIDENCE-TEST-1',
                    'legal_phone': '+2250705060709',
                    'establishment_address': 'Cocody',
                    'establishment_city': 'Abidjan',
                    'number_of_rooms': '5',
                    'type_piece_identite': 'cni',
                    'numero_piece_identite': 'CI-RESIDENCE-ID-1',
                    'legal_document': SimpleUploadedFile(
                        'legal.pdf',
                        b'%PDF-1.4 test document',
                        content_type='application/pdf',
                    ),
                    'establishment_photo': SimpleUploadedFile(
                        'residence.jpg',
                        image_bytes.getvalue(),
                        content_type='image/jpeg',
                    ),
                },
            )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(
            recipient=administrator,
            notification_type='system',
            title='Nouvelle inscription',
        )
        self.assertIn('Résidence test', notification.message)
        self.assertTrue(any('nouvelle inscription' in message.subject.lower() for message in mail.outbox))
        send_sms_mock.assert_called_once()

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

    def test_password_reset_confirm_redirects_to_complete_page(self):
        user = User.objects.create_user(
            username='reset_confirm_test',
            email='reset.confirm@example.com',
            password='StrongPassword123!'
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token}),
            {'new_password1': 'NewStrongPassword456!', 'new_password2': 'NewStrongPassword456!'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewStrongPassword456!'))
        self.assertTrue(self.client.login(
            username=user.email,
            password='NewStrongPassword456!',
        ))
        self.assertIsNotNone(authenticate(
            username=user.username.upper(),
            password='NewStrongPassword456!',
        ))

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

    def test_verified_professional_profile_does_not_claim_publication_is_allowed_before_establishment_review(self):
        user = User.objects.create_user(
            username='verified_residence_profile',
            email='verified.residence.profile@example.com',
            password='StrongPassword123!',
        )
        profile = user.profile
        profile.account_type = 'residence'
        profile.verified = True
        profile.verification_status = 'verified'
        profile.save(update_fields=['account_type', 'verified', 'verification_status'])
        ProfessionalProfile.objects.create(
            profile=profile,
            establishment_type='residence',
            establishment_name='Résidence test',
            siret_or_rccm='CI-TEST-VERIFIED-RESIDENCE',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=1,
            legal_document='legal/test.pdf',
            establishment_photo='facade/test.jpg',
        )
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file='identity.jpg',
                status='verified',
            )
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:profil'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identité vérifiée — publication indisponible')
        self.assertContains(response, 'Vos pièces d’établissement sont en attente')
        self.assertContains(response, 'La vérification de l’identité ne valide pas automatiquement')
        self.assertContains(response, reverse('accounts:verification_docs'))
        self.assertNotContains(response, 'Vous pouvez publier des annonces sans restriction')

        professional_profile = profile.professional_profile
        professional_profile.is_verified = True
        professional_profile.save(update_fields=['is_verified'])
        response = self.client.get(reverse('accounts:profil'))

        self.assertContains(response, 'Vous pouvez publier des annonces sans restriction')

    def test_residence_dashboard_renders_without_professional_profile(self):
        user = User.objects.create_user(
            username='residence_without_professional_profile',
            email='residence.dashboard@example.com',
            password='StrongPassword123!',
        )
        user.profile.account_type = 'residence'
        user.profile.save(update_fields=['account_type'])
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:dashboard_residence'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ma Résidence')
        for route_name in (
            'logement:gestion_logements',
            'logement:calendrier_reservations',
            'logement:mes_paiements',
            'logement:statistiques',
            'logement:avis_clients',
        ):
            self.assertContains(response, reverse(route_name))

    def test_professional_dashboards_show_verified_establishment_status(self):
        for account_type, dashboard_url in (
            ('hotel', 'accounts:dashboard_hotel'),
            ('residence', 'accounts:dashboard_residence'),
        ):
            with self.subTest(account_type=account_type):
                user = User.objects.create_user(
                    username=f'{account_type}_verified_dashboard',
                    email=f'{account_type}.verified.dashboard@example.com',
                    password='StrongPassword123!',
                )
                profile = user.profile
                profile.account_type = account_type
                profile.save(update_fields=['account_type'])
                ProfessionalProfile.objects.create(
                    profile=profile,
                    establishment_type=account_type,
                    establishment_name=f'Établissement {account_type}',
                    siret_or_rccm=f'CI-TEST-{account_type}',
                    legal_representative='Responsable test',
                    legal_phone='+22501020304',
                    establishment_address='Adresse test',
                    establishment_city='Abidjan',
                    number_of_rooms=1,
                    legal_document='legal/test.pdf',
                    establishment_photo='facade/test.jpg',
                    is_verified=True,
                )
                self.client.force_login(user)

                response = self.client.get(reverse(dashboard_url))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Compte vérifié')
                self.client.logout()

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

    def test_authentication_does_not_activate_pending_account_with_valid_credentials(self):
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

        self.assertIsNone(authenticated_user)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_email_activation_alone_does_not_activate_account(self):
        user = User.objects.create_user(
            username='email_only_test',
            email='email.only@example.com',
            password='StrongPassword123!',
        )
        user.is_active = False
        user.save(update_fields=['is_active'])
        profile = user.profile
        profile.activation_token = 'email-token'
        profile.activation_token_created_at = timezone.now()
        profile.save(update_fields=['activation_token', 'activation_token_created_at'])
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.get(reverse(
            'accounts:activate_account',
            kwargs={'uidb64': uidb64, 'token': 'email-token'},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adresse email vérifiée')
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(profile.email_verified)
        self.assertFalse(profile.phone_verified)
        self.assertFalse(user.is_active)

    def test_phone_activation_alone_does_not_activate_account(self):
        user = User.objects.create_user(
            username='phone_only_test',
            email='phone.only@example.com',
            password='StrongPassword123!',
        )
        user.is_active = False
        user.save(update_fields=['is_active'])
        profile = user.profile
        profile.phone_verification_code = '123456'
        profile.phone_verification_created_at = timezone.now()
        profile.activation_token = 'phone-token'
        profile.activation_token_created_at = timezone.now()
        profile.save(update_fields=[
            'phone_verification_code',
            'phone_verification_created_at',
            'activation_token',
            'activation_token_created_at',
        ])
        session = self.client.session
        session['pending_user_id'] = user.pk
        session.save()

        response = self.client.post(
            reverse('accounts:verify_phone'),
            {'code': '123456'},
        )

        self.assertRedirects(response, reverse('accounts:inscription_pending'))
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(profile.phone_verified)
        self.assertFalse(profile.email_verified)
        self.assertFalse(user.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(reverse(
            'accounts:activate_account',
            kwargs={'uidb64': uidb64, 'token': 'phone-token'},
        ))
        self.assertContains(response, 'Compte activé')
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_account_activates_only_after_both_email_and_phone_are_verified(self):
        user = User.objects.create_user(
            username='both_channels_test',
            email='both.channels@example.com',
            password='StrongPassword123!',
        )
        user.is_active = False
        user.save(update_fields=['is_active'])
        profile = user.profile
        profile.activation_token = 'both-token'
        profile.activation_token_created_at = timezone.now()
        profile.save(update_fields=['activation_token', 'activation_token_created_at'])
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        self.client.get(reverse(
            'accounts:activate_account',
            kwargs={'uidb64': uidb64, 'token': 'both-token'},
        ))

        profile.refresh_from_db()
        profile.phone_verification_code = '654321'
        profile.phone_verification_created_at = timezone.now()
        profile.save(update_fields=['phone_verification_code', 'phone_verification_created_at'])
        session = self.client.session
        session['pending_user_id'] = user.pk
        session.save()

        response = self.client.post(reverse('accounts:verify_phone'), {'code': '654321'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accounts:dashboard'))
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(profile.email_verified)
        self.assertTrue(profile.phone_verified)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    @override_settings(DEBUG=False, SMS_BACKEND='console')
    def test_console_sms_cannot_verify_a_phone_in_production(self):
        self.assertFalse(send_sms('+22501020304', 'Code de test'))

    @mock.patch('accounts.views.send_sms', return_value=True)
    def test_resend_phone_code_refuses_ambiguous_phone_number(self, send_sms_mock):
        users = [
            User.objects.create_user(username=f'duplicate_phone_{index}')
            for index in range(2)
        ]
        for user in users:
            profile = user.profile
            profile.telephone = '0103280809'
            profile.phone_verification_code = '123456'
            profile.save(update_fields=['telephone', 'phone_verification_code'])

        response = self.client.post(
            reverse('accounts:resend_phone_code'),
            {'phone': '0103280809'},
            follow=True,
        )

        self.assertContains(
            response,
            'Plusieurs comptes sont associés à ce numéro',
            status_code=200,
        )
        send_sms_mock.assert_not_called()
        for user in users:
            user.profile.refresh_from_db()
            self.assertEqual(user.profile.phone_verification_code, '123456')

    @mock.patch('accounts.views.send_sms', return_value=True)
    def test_resend_phone_code_works_for_a_unique_phone_number(self, send_sms_mock):
        user = User.objects.create_user(username='unique_phone_user')
        user.is_active = False
        user.save(update_fields=['is_active'])
        profile = user.profile
        profile.telephone = '0103280809'
        profile.save(update_fields=['telephone'])

        response = self.client.post(
            reverse('accounts:resend_phone_code'),
            {'phone': '0103280809'},
        )

        self.assertRedirects(response, reverse('accounts:verify_phone'))
        send_sms_mock.assert_called_once()
        self.assertEqual(send_sms_mock.call_args.args[0], '0103280809')
        profile.refresh_from_db()
        self.assertEqual(profile.phone_verification_code, send_sms_mock.call_args.args[1].split(': ')[1])
        self.assertEqual(self.client.session['pending_user_id'], user.pk)


class ProfessionalDashboardConsistencyTests(TestCase):
    def test_dashboard_uses_live_stay_payment_and_review_data(self):
        from logement.models import AvisLogement, Logement, Paiement, Reservation

        owner = User.objects.create_user(
            username='hotel_dashboard_owner',
            email='hotel.dashboard.owner@example.com',
            password='StrongPassword123!',
        )
        owner.profile.account_type = 'hotel'
        owner.profile.save(update_fields=['account_type'])
        guest = User.objects.create_user(
            username='hotel_dashboard_guest',
            email='hotel.dashboard.guest@example.com',
            first_name='Aminata',
            last_name='Diallo',
            password='StrongPassword123!',
        )
        logement = Logement.objects.create(
            titre='Hôtel dashboard',
            description='Chambres de test',
            ville='Abidjan',
            account_type='hotel',
            unites_totales=2,
            proprietaire=owner,
        )
        today = timezone.localdate()
        reservation = Reservation.objects.create(
            logement=logement,
            client_user=guest,
            client_nom='Aminata Diallo',
            client_email=guest.email,
            client_telephone='+2250700000000',
            date_arrivee=today - timedelta(days=1),
            date_depart=today + timedelta(days=1),
            nombre_personnes=1,
            nombre_chambres=1,
            prix_par_nuit=25000,
            nombre_nuits=2,
            prix_total=50000,
            montant_final=50000,
            statut='checked_in',
        )
        reservation.unites.set(logement.unites.filter(numero='1'))
        Paiement.objects.create(
            reservation=reservation,
            montant=25000,
            methode='cash',
            statut='completed',
            completed_at=timezone.now(),
        )
        AvisLogement.objects.create(
            logement=logement,
            reservation=reservation,
            auteur=guest,
            note_logement=5,
            note_proprietaire=5,
            commentaire='Excellent séjour.',
        )
        self.client.force_login(owner)

        response = self.client.get(reverse('accounts:dashboard_hotel'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_chambres'], 2)
        self.assertEqual(response.context['chambres_disponibles'], 1)
        self.assertEqual(response.context['nb_clients_actifs'], 1)
        self.assertEqual(response.context['taux_occupation'], 50)
        self.assertEqual(response.context['revenu_mois'], 25000)
        self.assertEqual(response.context['note_moyenne'], 5)
        self.assertEqual(response.context['nb_avis'], 1)
        self.assertEqual(response.context['recent_reservations'][0].pk, reservation.pk)
        self.assertContains(response, 'Aminata Diallo')
        self.assertContains(response, 'En séjour')
        self.assertContains(response, reverse('logement:mes_paiements'))
        self.assertContains(response, reverse('logement:statistiques'))
        self.assertContains(response, reverse('logement:avis_clients'))


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
                                color=(20 + index * 50, 80, 140),
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

    def test_complete_identity_upload_shows_waiting_for_manual_review_message(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            for index, document_type in enumerate(('id_front', 'id_back', 'selfie')):
                response = self.client.post(
                    reverse('accounts:upload_document'),
                    {
                        'document_type': document_type,
                        'document_file': self.make_image_upload(
                            f'{document_type}.jpg',
                            color=(30 + index * 60, 80, 140),
                        ),
                    },
                    follow=index == 2,
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dossier complet — vérification en cours')
        self.assertContains(response, 'Vous recevrez une notification et un e-mail')
        self.assertContains(response, 'Notre équipe va vérifier vos informations')

    def test_verification_page_shows_existing_document_review_statuses(self):
        DocumentVerification.objects.create(
            profile=self.user.profile,
            document_type='id_front',
            document_file='identity-front.jpg',
            status='verified',
        )
        DocumentVerification.objects.create(
            profile=self.user.profile,
            document_type='selfie',
            document_file='identity-selfie.jpg',
            status='pending',
        )

        response = self.client.get(reverse('accounts:verification_docs'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['document_statuses'],
            {'id_front': 'verified', 'selfie': 'pending'},
        )
        self.assertContains(response, 'document-statuses')

    def test_flagged_profile_can_upload_missing_documents_to_resume_review(self):
        profile = self.user.profile
        profile.verification_status = 'flagged'
        profile.save(update_fields=['verification_status'])

        page_response = self.client.get(reverse('accounts:verification_docs'))
        self.assertEqual(page_response.status_code, 200)
        self.assertContains(page_response, 'file-id_back')
        self.assertContains(page_response, 'file-selfie')
        self.assertContains(page_response, 'vous pouvez compléter votre dossier')

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse('accounts:upload_document'),
                {
                    'document_type': 'id_back',
                    'document_file': self.make_image_upload('id-back.jpg', color=(220, 40, 100)),
                },
            )

        self.assertRedirects(response, reverse('accounts:verification_docs'))
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, 'pending')
        self.assertFalse(profile.verified)
        self.assertTrue(
            DocumentVerification.objects.filter(
                profile=profile,
                document_type='id_back',
                status='pending',
            ).exists()
        )

    def test_publication_requires_all_three_identity_documents_to_be_approved(self):
        profile = self.user.profile
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=['verification_status', 'verified'])

        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file='identity.jpg',
                status='verified',
            )

        profile.refresh_from_db()
        self.assertTrue(profile.can_publish)

        DocumentVerification.objects.filter(
            profile=profile,
            document_type='id_back',
        ).update(status='pending')
        self.assertFalse(profile.can_publish)

    def test_tourist_cannot_publish_even_after_identity_verification(self):
        profile = self.user.profile
        profile.account_type = 'individu'
        profile.role = 'touriste'
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=['account_type', 'role', 'verification_status', 'verified'])
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file='identity.jpg',
                status='verified',
            )

        self.assertFalse(profile.can_publish)
        self.assertIn('Touriste', profile.publication_block_reason)

    def test_professional_publication_also_requires_establishment_review(self):
        profile = self.user.profile
        profile.account_type = 'hotel'
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=['account_type', 'verification_status', 'verified'])
        ProfessionalProfile.objects.create(
            profile=profile,
            establishment_type='hotel',
            establishment_name='Hôtel test',
            siret_or_rccm='CI-TEST-123',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=1,
            legal_document='legal.pdf',
            establishment_photo='facade.jpg',
        )
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file='identity.jpg',
                status='verified',
            )

        self.assertFalse(profile.can_publish)
        profile.professional_profile.is_verified = True
        profile.professional_profile.save(update_fields=['is_verified'])
        self.assertTrue(profile.can_publish)
