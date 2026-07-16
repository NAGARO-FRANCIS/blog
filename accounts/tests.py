from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone


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
