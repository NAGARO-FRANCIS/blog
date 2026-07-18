from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Reservation, Logement


class PaymentViewTests(TestCase):
    def test_payment_page_loads_without_stripe_installed(self):
        owner = User.objects.create_user(username='owner_test', email='owner@example.com', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Villa test',
            description='Description test',
            ville='Abidjan',
            quartier='Plateaux',
            account_type='hotel',
            prix_par_nuit=10000,
            nombre_chambres=1,
            proprietaire=owner,
        )
        reservation = Reservation.objects.create(
            logement=logement,
            client_nom='Client Test',
            client_email='client@example.com',
            client_telephone='+2250700000000',
            date_arrivee='2026-07-18',
            date_depart='2026-07-20',
            nombre_personnes=1,
            nombre_chambres=1,
            prix_par_nuit=10000,
            nombre_nuits=2,
            prix_total=20000,
            frais_service=1000,
            frais_nettoyage_reservation=500,
            montant_final=21500,
        )

        response = self.client.get(reverse('logement:paiement', args=[reservation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paiement de votre réservation')
