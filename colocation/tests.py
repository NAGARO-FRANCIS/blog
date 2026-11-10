from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from logement.models import Logement
from .models import ColocationAnnonce


class PublicationVerificationTests(TestCase):
    def test_tourist_cannot_publish_a_colocation_announcement(self):
        tourist = User.objects.create_user(
            username='tourist_cannot_publish_colocation',
            password='StrongPassword123!',
        )
        tourist.profile.account_type = 'individu'
        tourist.profile.role = 'touriste'
        tourist.profile.save(update_fields=['account_type', 'role'])
        self.client.force_login(tourist)

        response = self.client.post(reverse('colocation:publier_annonce'), {})

        self.assertRedirects(response, reverse('colocation:liste_annonces'))
        self.assertFalse(ColocationAnnonce.objects.filter(proprietaire=tourist).exists())

    def test_unverified_owner_cannot_publish_colocation_announcement(self):
        owner = User.objects.create_user(
            username='unverified_colocation_owner',
            password='StrongPassword123!',
        )
        owner.profile.account_type = 'individu'
        owner.profile.role = 'proprietaire'
        owner.profile.save(update_fields=['account_type', 'role'])
        self.client.force_login(owner)

        response = self.client.post(reverse('colocation:publier_annonce'), {})

        self.assertRedirects(response, reverse('accounts:verification_docs'))


class HomeViewTests(TestCase):
    def test_home_renders_shared_feed_with_count_and_pagination(self):
        for index in range(13):
            Logement.objects.create(
                titre=f'Annonce {index}',
                description='Description test',
                ville='Abidjan',
                account_type='individu',
            )

        response = self.client.get(reverse('colocation:colocation_home'))
        root_response = self.client.get('/')
        next_page = self.client.get(
            reverse('colocation:colocation_home'),
            {'page': '2'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_annonces'], 13)
        self.assertEqual(len(response.context['annonces']), 12)
        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(root_response.context['total_annonces'], 13)
        self.assertEqual(next_page.status_code, 200)
        self.assertEqual(len(next_page.context['annonces']), 1)
