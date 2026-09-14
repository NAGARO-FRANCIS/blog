from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RechercheLogementForm
from .models import AvisLogement, Reservation, Logement
from .views import _apply_logement_filters


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


class AvisLogementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner_reviews', password='StrongPassword123!')
        self.client_user = User.objects.create_user(username='client_reviews', password='StrongPassword123!')
        self.logement = Logement.objects.create(
            titre='Appartement avis',
            description='Description',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
            proprietaire=self.owner,
        )

    def make_reservation(self, statut='completed', date_depart='2026-09-10'):
        return Reservation.objects.create(
            logement=self.logement,
            client_user=self.client_user,
            client_nom='Client Reviews',
            client_email='reviews@example.com',
            client_telephone='+2250700000000',
            date_arrivee='2026-09-07',
            date_depart=date_depart,
            nombre_personnes=1,
            nombre_chambres=1,
            prix_par_nuit=10000,
            nombre_nuits=3,
            prix_total=30000,
            montant_final=30000,
            statut=statut,
        )

    def test_un_client_ayant_termine_son_sejour_peut_publier(self):
        reservation = self.make_reservation()
        self.client.login(username='client_reviews', password='StrongPassword123!')

        response = self.client.post(
            reverse('logement:ajouter_avis', args=[self.logement.id]),
            {'note_logement': 5, 'note_proprietaire': 4, 'commentaire': 'Excellent séjour.'},
        )

        self.assertRedirects(response, reverse('logement:detail_logement', args=[self.logement.id]))
        self.assertTrue(AvisLogement.objects.filter(reservation=reservation, auteur=self.client_user).exists())

    def test_un_client_avec_sejour_non_termine_ne_peut_pas_publier(self):
        self.make_reservation(statut='confirmed', date_depart='2099-09-10')
        self.client.login(username='client_reviews', password='StrongPassword123!')

        self.client.post(
            reverse('logement:ajouter_avis', args=[self.logement.id]),
            {'note_logement': 5, 'note_proprietaire': 5, 'commentaire': 'Avis interdit.'},
        )

        self.assertFalse(AvisLogement.objects.exists())


class RechercheLogementTests(TestCase):
    def test_filtre_avance_par_commune_prix_et_equipements(self):
        matching = Logement.objects.create(
            titre='Studio proche université',
            description='Meublé et connecté',
            ville='Abidjan',
            commune='Cocody',
            quartier='Angré',
            type_logement='studio',
            prix=150000,
            nombre_chambres=1,
            meuble=True,
            wifi=True,
            eau=True,
            electricite=True,
        )
        Logement.objects.create(
            titre='Appartement éloigné',
            description='Autre annonce',
            ville='Abidjan',
            commune='Yopougon',
            type_logement='appartement',
            prix=200000,
            nombre_chambres=2,
        )

        form = RechercheLogementForm({
            'commune': 'Cocody',
            'quartier': 'Angré',
            'prix_max': '150000',
            'type_logement': 'studio',
            'wifi': '1',
            'meuble': '1',
        })

        self.assertTrue(form.is_valid())
        results = _apply_logement_filters(Logement.objects.all(), form.cleaned_data)
        self.assertEqual(list(results), [matching])
