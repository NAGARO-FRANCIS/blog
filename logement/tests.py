from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RechercheLogementForm
from .models import AvisLogement, Paiement, Reservation, Logement
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
        session = self.client.session
        session['guest_reservation_ids'] = [reservation.id]
        session.save()

        response = self.client.get(reverse('logement:paiement', args=[reservation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paiement de votre réservation')

    def test_anonymous_user_cannot_pay_another_reservations_by_id(self):
        owner = User.objects.create_user(username='owner_payment_test', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Villa protégée',
            description='Description test',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
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
            montant_final=20000,
        )

        response = self.client.post(
            reverse('logement:paiement', args=[reservation.id]),
            {'payment_method': 'cash'},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(reservation.__class__.objects.get(pk=reservation.pk).statut, 'pending')
        self.assertFalse(Paiement.objects.filter(reservation=reservation).exists())

    def test_anonymous_user_cannot_open_another_reservations_confirmation(self):
        owner = User.objects.create_user(username='owner_confirmation_test', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Villa privée',
            description='Description test',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
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
            montant_final=20000,
        )

        response = self.client.get(
            reverse('logement:confirmation_reservation', args=[reservation.id])
        )

        self.assertRedirects(response, reverse('accounts:login'))


class ReservationSecurityTests(TestCase):
    def test_reservation_utilise_le_prix_legacy_si_prix_par_nuit_est_vide(self):
        logement = Logement.objects.create(
            titre='Annonce legacy',
            description='Description test',
            ville='Abidjan',
            quartier='Plateaux',
            account_type='hotel',
            prix=10000,
            proprietaire=User.objects.create_user(
                username='owner_legacy',
                password='StrongPassword123!',
            ),
        )

        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement.id]),
            {
                'date_arrivee': '2026-10-10',
                'date_depart': '2026-10-12',
                'nombre_personnes': 1,
                'nombre_chambres': 1,
                'client_nom': 'Client Legacy',
                'client_email': 'legacy@example.com',
                'client_telephone': '+2250700000000',
                'remarques': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get(logement=logement)
        self.assertEqual(reservation.prix_par_nuit, 10000)
        self.assertEqual(reservation.montant_final, 20000)
        self.assertIn(reservation.id, self.client.session['guest_reservation_ids'])

    def test_un_proprietaire_ne_peut_pas_reserver_son_propre_logement(self):
        owner = User.objects.create_user(username='owner_resa', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Villa du propriétaire',
            description='Description test',
            ville='Abidjan',
            quartier='Plateaux',
            account_type='hotel',
            prix_par_nuit=15000,
            nombre_chambres=1,
            proprietaire=owner,
        )

        self.client.login(username='owner_resa', password='StrongPassword123!')
        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement.id]),
            {
                'date_arrivee': '2026-10-10',
                'date_depart': '2026-10-12',
                'nombre_personnes': 2,
                'nombre_chambres': 1,
                'client_nom': 'Owner Test',
                'client_email': 'owner@example.com',
                'client_telephone': '+2250700000000',
                'remarques': 'Essai interdit',
            },
        )

        self.assertEqual(Reservation.objects.filter(logement=logement).count(), 0)
        self.assertContains(response, 'Vous ne pouvez pas réserver votre propre annonce')

    def test_reservations_concurrentes_sont_attribuees_a_des_chambres_distinctes(self):
        owner = User.objects.create_user(username='owner_inventory', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Hôtel deux chambres',
            description='Description test',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
            unites_totales=2,
            proprietaire=owner,
        )
        url = reverse('logement:reserver_logement', args=[logement.id])
        reservation_data = {
            'date_arrivee': '2026-10-10',
            'date_depart': '2026-10-12',
            'nombre_personnes': 1,
            'nombre_chambres': 1,
            'client_nom': 'Client Test',
            'client_email': 'client@example.com',
            'client_telephone': '+2250700000000',
            'remarques': '',
        }

        first_response = self.client.post(url, reservation_data)
        second_response = self.client.post(url, reservation_data)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        reservations = list(Reservation.objects.filter(logement=logement).order_by('id'))
        self.assertEqual(len(reservations), 2)
        self.assertEqual(reservations[0].unites.count(), 1)
        self.assertEqual(reservations[1].unites.count(), 1)
        self.assertNotEqual(
            reservations[0].unites.get().pk,
            reservations[1].unites.get().pk,
        )

        full_response = self.client.post(url, reservation_data)

        self.assertEqual(full_response.status_code, 200)
        self.assertContains(full_response, 'Il ne reste pas assez de chambres')
        self.assertEqual(Reservation.objects.filter(logement=logement).count(), 2)


class ReservationListViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='hotel_owner',
            password='StrongPassword123!',
        )
        self.owner.profile.account_type = 'hotel'
        self.owner.profile.save()
        self.logement = Logement.objects.create(
            titre='Chambre vue mer',
            description='Chambre de test',
            ville='Abidjan',
            account_type='hotel',
            proprietaire=self.owner,
        )
        self.client_user = User.objects.create_user(
            username='reservation_client',
            first_name='Aminata',
            last_name='Diallo',
            email='aminata@example.com',
            password='StrongPassword123!',
        )
        self.reservation = Reservation.objects.create(
            logement=self.logement,
            client_user=self.client_user,
            client_nom='Aminata Diallo',
            client_email='aminata@example.com',
            client_telephone='+2250700000000',
            date_arrivee='2026-10-10',
            date_depart='2026-10-12',
            nombre_personnes=2,
            nombre_chambres=1,
            prix_par_nuit=10000,
            nombre_nuits=2,
            prix_total=20000,
            montant_final=20000,
            statut='confirmed',
            paye=True,
        )
        self.reservation.unites.set(self.logement.unites.filter(numero='1'))
        self.client.login(username='hotel_owner', password='StrongPassword123!')

    def test_reservations_affichent_client_chambre_sejour_et_statut(self):
        response = self.client.get(reverse('logement:mes_reservations'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aminata Diallo')
        self.assertContains(response, 'Chambre vue mer')
        self.assertContains(response, '10/10/2026')
        self.assertContains(response, '12/10/2026')
        self.assertContains(response, '1 chambre réservée')
        self.assertContains(response, 'Chambre n° 1')
        self.assertContains(response, 'Payée')

    def test_recherche_et_filtre_statut_sont_appliques(self):
        response = self.client.get(
            reverse('logement:mes_reservations'),
            {'q': 'aminata@example.com', 'statut': 'confirmed'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aminata Diallo')
        self.assertEqual(response.context['nb_reservations'], 1)


class ReservationCalendarTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='calendar_owner',
            password='StrongPassword123!',
        )
        self.owner.profile.account_type = 'hotel'
        self.owner.profile.save()
        self.logement = Logement.objects.create(
            titre='Chambres du calendrier',
            description='Logement de test',
            ville='Abidjan',
            account_type='hotel',
            unites_totales=3,
            proprietaire=self.owner,
        )
        self.client.login(username='calendar_owner', password='StrongPassword123!')

    def create_reservation(self, name, arrival, departure, rooms, status='confirmed'):
        return Reservation.objects.create(
            logement=self.logement,
            client_nom=name,
            client_email=f'{name.lower().replace(" ", ".")}@example.com',
            client_telephone='+2250700000000',
            date_arrivee=arrival,
            date_depart=departure,
            nombre_personnes=rooms,
            nombre_chambres=rooms,
            prix_par_nuit=10000,
            nombre_nuits=(date.fromisoformat(departure) - date.fromisoformat(arrival)).days,
            prix_total=10000,
            montant_final=10000,
            statut=status,
        )

    def test_calendrier_indique_chambres_occupees_et_reservations_par_date(self):
        confirmed = self.create_reservation('Client Confirme', '2026-10-10', '2026-10-12', 2)
        confirmed.unites.set(self.logement.unites.filter(numero__in=['1', '2']))
        pending = self.create_reservation('Client Attente', '2026-10-11', '2026-10-13', 1, 'pending')
        pending.unites.set(self.logement.unites.filter(numero='3'))
        self.create_reservation('Client Annule', '2026-10-11', '2026-10-13', 1, 'cancelled')

        response = self.client.get(
            reverse('logement:calendrier_reservations'),
            {'year': 2026, 'month': 10, 'logement': self.logement.id},
        )

        self.assertEqual(response.status_code, 200)
        days = {day['number']: day for day in response.context['days'] if day}
        self.assertEqual(days[10]['reserved_units'], 2)
        self.assertEqual(days[11]['reserved_units'], 3)
        self.assertEqual(days[11]['available_units'], 0)
        self.assertEqual(days[12]['reserved_units'], 1)
        self.assertEqual(days[13]['reserved_units'], 0)
        self.assertContains(response, 'Client Confirme')
        self.assertContains(response, 'Client Attente')
        self.assertContains(response, 'n°1')
        self.assertContains(response, 'n°2')
        self.assertContains(response, 'n°3')
        self.assertNotContains(response, 'Client Annule')


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
