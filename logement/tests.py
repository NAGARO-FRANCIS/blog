from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import (
    LogementHotelForm,
    LogementResidenceForm,
    RechercheLogementForm,
    ReservationForm,
)
from accounts.models import DocumentVerification, ProfessionalProfile
from .models import AvisLogement, Etablissement, Paiement, Reservation, Logement
from .views import _apply_logement_filters


class PublicationVerificationTests(TestCase):
    def test_tourist_cannot_publish_a_lodging_listing(self):
        tourist = User.objects.create_user(
            username='tourist_cannot_publish',
            password='StrongPassword123!',
        )
        tourist.profile.account_type = 'individu'
        tourist.profile.role = 'touriste'
        tourist.profile.save(update_fields=['account_type', 'role'])
        self.client.force_login(tourist)

        response = self.client.post(reverse('logement:ajouter_logement'), {})

        self.assertRedirects(response, reverse('logement:home'))
        self.assertFalse(Logement.objects.filter(proprietaire=tourist).exists())

    def test_unverified_owner_cannot_open_lodging_publication_form(self):
        owner = User.objects.create_user(
            username='unverified_lodging_owner',
            password='StrongPassword123!',
        )
        owner.profile.account_type = 'individu'
        owner.profile.role = 'proprietaire'
        owner.profile.save(update_fields=['account_type', 'role'])
        self.client.force_login(owner)

        response = self.client.post(reverse('logement:ajouter_logement'), {})

        self.assertRedirects(response, reverse('accounts:verification_docs'))
        self.assertFalse(Logement.objects.filter(proprietaire=owner).exists())

    def create_verified_residence_owner(self, establishment_verified):
        owner = User.objects.create_user(
            username=f'residence_owner_{establishment_verified}',
            password='StrongPassword123!',
        )
        profile = owner.profile
        profile.account_type = 'residence'
        profile.role = 'proprietaire'
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=[
            'account_type',
            'role',
            'verification_status',
            'verified',
        ])
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )
        ProfessionalProfile.objects.create(
            profile=profile,
            establishment_type='residence',
            establishment_name='Résidence test',
            siret_or_rccm=f'CI-TEST-{establishment_verified}',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=3,
            legal_document='legal/test.pdf',
            establishment_photo='facade/test.jpg',
            is_verified=establishment_verified,
        )
        return owner

    def test_professional_publication_explains_that_establishment_review_is_pending(self):
        owner = self.create_verified_residence_owner(establishment_verified=False)
        self.client.force_login(owner)

        response = self.client.get(reverse('logement:ajouter_logement'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vos pièces d’établissement sont en attente')
        self.assertFalse(Logement.objects.filter(proprietaire=owner).exists())

    def test_professional_owner_can_open_listing_form_after_both_reviews(self):
        owner = self.create_verified_residence_owner(establishment_verified=True)
        Etablissement.objects.create(
            proprietaire=owner,
            nom='Résidence test',
            type_etablissement='residence',
            ville='Abidjan',
        )
        self.client.force_login(owner)

        response = self.client.get(reverse('logement:ajouter_logement'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('etablissement_form', response.context)

    def test_owner_can_publish_multiple_listings_and_find_add_button_again(self):
        owner = User.objects.create_user(
            username='multiple_listing_owner',
            password='StrongPassword123!',
        )
        profile = owner.profile
        profile.account_type = 'individu'
        profile.role = 'proprietaire'
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=[
            'account_type',
            'role',
            'verification_status',
            'verified',
        ])
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )
        self.client.force_login(owner)

        for title in ('Première annonce', 'Deuxième annonce'):
            response = self.client.post(
                reverse('logement:ajouter_logement'),
                {
                    'titre': title,
                    'description': 'Description du logement',
                    'type_logement': 'appartement',
                    'prix': '35000',
                    'ville': 'Abidjan',
                    'quartier': 'Cocody',
                    'photos-TOTAL_FORMS': '0',
                    'photos-INITIAL_FORMS': '0',
                    'photos-MIN_NUM_FORMS': '0',
                    'photos-MAX_NUM_FORMS': '1000',
                    'videos-TOTAL_FORMS': '0',
                    'videos-INITIAL_FORMS': '0',
                    'videos-MIN_NUM_FORMS': '0',
                    'videos-MAX_NUM_FORMS': '1000',
                },
            )
            self.assertRedirects(response, reverse('logement:mes_logements'))

        self.assertEqual(Logement.objects.filter(proprietaire=owner).count(), 2)
        listings_response = self.client.get(reverse('logement:mes_logements'))
        self.assertEqual(listings_response.status_code, 200)
        self.assertContains(listings_response, 'Première annonce')
        self.assertContains(listings_response, 'Deuxième annonce')
        self.assertContains(listings_response, 'Publier une autre annonce')

        dashboard_response = self.client.get(reverse('accounts:dashboard_individu'))
        self.assertContains(dashboard_response, 'Publier une annonce')
        self.assertContains(dashboard_response, 'Voir toutes')


class PaymentViewTests(TestCase):
    def test_hotel_payment_page_redirects_to_confirmation(self):
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
            date_arrivee=date(2026, 7, 18),
            date_depart=date(2026, 7, 20),
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

        self.assertRedirects(
            response,
            reverse('logement:confirmation_reservation', args=[reservation.id]),
        )

    def test_hotel_reservation_cannot_start_online_payment(self):
        owner = User.objects.create_user(username='owner_online_payment', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Hôtel paiement sur place',
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
            date_arrivee=date(2026, 7, 18),
            date_depart=date(2026, 7, 20),
            nombre_personnes=1,
            nombre_chambres=1,
            prix_par_nuit=10000,
            nombre_nuits=2,
            prix_total=20000,
            montant_final=20000,
        )
        Paiement.objects.create(
            reservation=reservation,
            montant=reservation.montant_final,
            methode='cash',
            statut='pending',
        )
        session = self.client.session
        session['guest_reservation_ids'] = [reservation.id]
        session.save()

        response = self.client.post(
            reverse('logement:paiement', args=[reservation.id]),
            {'payment_method': 'stripe'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            Paiement.objects.get(reservation=reservation).methode,
            'cash',
        )

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
    def test_reservations_hotel_et_residence_sont_confirmees_avec_paiement_sur_place(self):
        for account_type in ('hotel', 'residence'):
            with self.subTest(account_type=account_type):
                owner = User.objects.create_user(
                    username=f'owner_{account_type}_cash',
                    password='StrongPassword123!',
                )
                logement = Logement.objects.create(
                    titre=f'Logement {account_type}',
                    description='Description test',
                    ville='Abidjan',
                    account_type=account_type,
                    prix_par_nuit=10000,
                    proprietaire=owner,
                )

                response = self.client.post(
                    reverse('logement:reserver_logement', args=[logement.id]),
                    {
                        'date_arrivee': '2026-12-10',
                        'date_depart': '2026-12-12',
                        'nombre_personnes': 1,
                        'nombre_chambres': 1,
                        'client_nom': 'Client Test',
                        'client_email': 'client@example.com',
                        'client_telephone': '+2250700000000',
                        'remarques': '',
                    },
                )

                reservation = Reservation.objects.get(logement=logement)
                self.assertRedirects(
                    response,
                    reverse('logement:confirmation_reservation', args=[reservation.id]),
                )
                self.assertEqual(reservation.statut, 'confirmed')
                self.assertFalse(reservation.paye)
                paiement = Paiement.objects.get(reservation=reservation)
                self.assertEqual(paiement.methode, 'cash')
                self.assertEqual(paiement.statut, 'pending')
                self.assertEqual(paiement.montant, reservation.montant_final)
                confirmation = self.client.get(
                    reverse('logement:confirmation_reservation', args=[reservation.id])
                )
                self.assertContains(confirmation, 'Réglez le montant total')
                self.assertContains(confirmation, 'Informations du voyageur')
                self.assertContains(confirmation, 'Client Test')
                self.assertContains(confirmation, f'RES-{reservation.id}')
                self.assertContains(confirmation, 'Imprimer la fiche')

    def test_tarif_journalier_est_obligatoire_a_la_publication_professionnelle(self):
        self.assertTrue(LogementHotelForm().fields['prix_par_nuit'].required)
        self.assertEqual(str(LogementHotelForm().fields['prix_par_nuit'].min_value), '0.01')
        self.assertTrue(LogementResidenceForm().fields['prix_par_nuit'].required)
        self.assertEqual(str(LogementResidenceForm().fields['prix_par_nuit'].min_value), '0.01')

    def test_reservation_permet_de_choisir_une_categorie_et_applique_son_tarif(self):
        owner = User.objects.create_user(username='owner_categories', password='StrongPassword123!')
        etablissement = Etablissement.objects.create(
            proprietaire=owner,
            nom='Hôtel catégories',
            type_etablissement='hotel',
            ville='Abidjan',
        )
        logement_depart = Logement.objects.create(
            titre='Chambre simple',
            description='Chambre simple',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
            proprietaire=owner,
            etablissement=etablissement,
        )
        logement_choisi = Logement.objects.create(
            titre='Suite familiale',
            description='Suite familiale',
            ville='Abidjan',
            account_type='hotel',
            type_logement='familiale',
            prix_par_nuit=25000,
            proprietaire=owner,
            etablissement=etablissement,
        )

        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement_depart.id]),
            {
                'categorie_logement': logement_choisi.id,
                'date_arrivee': '2026-10-10',
                'date_depart': '2026-10-12',
                'nombre_personnes': 2,
                'nombre_chambres': 1,
                'client_nom': 'Client catégorie',
                'client_email': 'categories@example.com',
                'client_telephone': '+2250700000000',
                'remarques': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.logement, logement_choisi)
        self.assertEqual(reservation.prix_par_nuit, 25000)
        self.assertEqual(reservation.montant_final, 50000)

    def test_reservation_hotel_utilise_le_logement_ouvert_si_aucune_categorie_n_est_choisie(self):
        owner = User.objects.create_user(username='owner_hotel_default', password='StrongPassword123!')
        etablissement = Etablissement.objects.create(
            proprietaire=owner,
            nom='Hôtel sans sélection obligatoire',
            type_etablissement='hotel',
            ville='Abidjan',
        )
        logement = Logement.objects.create(
            titre='Chambre ouverte depuis sa fiche',
            description='Chambre standard',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=18000,
            proprietaire=owner,
            etablissement=etablissement,
        )
        Logement.objects.create(
            titre='Suite dans le même hôtel',
            description='Suite',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=35000,
            proprietaire=owner,
            etablissement=etablissement,
        )

        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement.id]),
            {
                'date_arrivee': '2026-11-10',
                'date_depart': '2026-11-12',
                'nombre_personnes': 1,
                'nombre_chambres': 1,
                'client_nom': 'Client hôtel',
                'client_email': 'hotel@example.com',
                'client_telephone': '+2250700000000',
                'remarques': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.logement, logement)
        self.assertEqual(reservation.prix_par_nuit, 18000)
        self.assertEqual(reservation.montant_final, 36000)

    def test_reservation_explique_quand_aucune_categorie_n_a_de_tarif(self):
        owner = User.objects.create_user(username='owner_no_daily_rate', password='StrongPassword123!')
        etablissement = Etablissement.objects.create(
            proprietaire=owner,
            nom='Résidence sans tarif journalier',
            type_etablissement='residence',
            ville='Abidjan',
        )
        logement = Logement.objects.create(
            titre='Studio mensuel',
            description='Studio',
            ville='Abidjan',
            account_type='residence',
            proprietaire=owner,
            etablissement=etablissement,
        )
        Logement.objects.create(
            titre='Appartement mensuel',
            description='Appartement',
            ville='Abidjan',
            account_type='residence',
            proprietaire=owner,
            etablissement=etablissement,
        )

        response = self.client.get(
            reverse('logement:reserver_logement', args=[logement.id])
        )
        form = response.context['form']

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('categorie_logement', form.fields)
        self.assertIn('tarif journalier', form.category_message)
        self.assertContains(response, form.category_message)

    def test_reservation_preselectionne_la_categorie_choisie_parmi_tarifs_mensuels_et_journaliers(self):
        owner = User.objects.create_user(username='owner_one_daily_rate', password='StrongPassword123!')
        etablissement = Etablissement.objects.create(
            proprietaire=owner,
            nom='Résidence avec un tarif journalier',
            type_etablissement='residence',
            ville='Abidjan',
        )
        logement_depart = Logement.objects.create(
            titre='Studio mensuel',
            description='Studio',
            ville='Abidjan',
            account_type='residence',
            prix_par_mois=200000,
            proprietaire=owner,
            etablissement=etablissement,
        )
        logement_reservable = Logement.objects.create(
            titre='Appartement à la nuitée',
            description='Appartement',
            ville='Abidjan',
            account_type='residence',
            prix_par_nuit=15000,
            proprietaire=owner,
            etablissement=etablissement,
        )

        form = ReservationForm(logement=logement_depart)

        self.assertIn('categorie_logement', form.fields)
        self.assertEqual(form.initial['categorie_logement'], logement_depart.pk)
        self.assertSetEqual(
            set(form.fields['categorie_logement'].queryset.values_list('pk', flat=True)),
            {logement_depart.pk, logement_reservable.pk},
        )

    def test_reservation_residence_utilise_le_tarif_journalier_et_non_le_mensuel(self):
        owner = User.objects.create_user(username='owner_residence_daily', password='StrongPassword123!')
        logement = Logement.objects.create(
            titre='Studio en résidence',
            description='Studio',
            ville='Abidjan',
            account_type='residence',
            prix_par_nuit=12000,
            prix_par_mois=200000,
            proprietaire=owner,
        )

        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement.id]),
            {
                'date_arrivee': '2026-10-10',
                'date_depart': '2026-10-11',
                'nombre_personnes': 1,
                'nombre_chambres': 1,
                'client_nom': 'Client résidence',
                'client_email': 'residence@example.com',
                'client_telephone': '+2250700000000',
                'remarques': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get(logement=logement)
        self.assertEqual(reservation.prix_par_nuit, 12000)
        self.assertEqual(reservation.montant_final, 12000)

    def test_reservation_residence_mensuelle_est_proratee_et_reservable_par_dates(self):
        owner = User.objects.create_user(username='owner_monthly_booking', password='StrongPassword123!')
        etablissement = Etablissement.objects.create(
            proprietaire=owner,
            nom='Résidence au tarif mensuel',
            type_etablissement='residence',
            ville='Abidjan',
        )
        logement_depart = Logement.objects.create(
            titre='Studio mensuel',
            description='Studio',
            ville='Abidjan',
            account_type='residence',
            prix_par_mois=200000,
            proprietaire=owner,
            etablissement=etablissement,
        )
        logement_choisi = Logement.objects.create(
            titre='Appartement mensuel',
            description='Appartement',
            ville='Abidjan',
            account_type='residence',
            prix_par_mois=300000,
            proprietaire=owner,
            etablissement=etablissement,
        )

        response = self.client.post(
            reverse('logement:reserver_logement', args=[logement_depart.id]),
            {
                'categorie_logement': logement_choisi.id,
                'date_arrivee': '2026-11-01',
                'date_depart': '2026-11-03',
                'nombre_personnes': 2,
                'nombre_chambres': 1,
                'client_nom': 'Client résidence mensuelle',
                'client_email': 'monthly@example.com',
                'client_telephone': '+2250700000000',
                'remarques': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get(logement=logement_choisi)
        self.assertEqual(str(reservation.prix_par_nuit), '10000.00')
        self.assertEqual(str(reservation.montant_final), '20000.00')

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

    def test_arrivee_et_depart_conservent_l_historique_et_liberent_la_chambre(self):
        url = reverse('logement:changer_statut_reservation', args=[self.reservation.pk])
        today = timezone.localdate()
        self.reservation.date_arrivee = today
        self.reservation.date_depart = today + timedelta(days=1)
        self.reservation.save(update_fields=['date_arrivee', 'date_depart', 'updated_at'])

        arrival_response = self.client.post(url, {'action': 'check_in'})

        self.assertRedirects(arrival_response, reverse('logement:mes_reservations'))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.statut, 'checked_in')
        self.assertEqual(self.logement.reserved_units_for_date(today), 1)
        self.assertEqual(self.logement.available_units_for_date(today), 0)

        duplicate_arrival_response = self.client.post(url, {'action': 'check_in'})
        self.assertRedirects(duplicate_arrival_response, reverse('logement:mes_reservations'))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.statut, 'checked_in')

        departure_response = self.client.post(url, {'action': 'check_out'})

        self.assertRedirects(departure_response, reverse('logement:mes_reservations'))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.statut, 'completed')
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())
        self.assertEqual(self.logement.reserved_units_for_date(today), 0)
        self.assertEqual(self.logement.available_units_for_date(today), 1)

    def test_seul_le_proprietaire_peut_cloturer_une_reservation(self):
        other_owner = User.objects.create_user(
            username='other_hotel_owner',
            password='StrongPassword123!',
        )
        self.client.force_login(other_owner)

        response = self.client.post(
            reverse('logement:changer_statut_reservation', args=[self.reservation.pk]),
            {'action': 'check_out'},
        )

        self.assertEqual(response.status_code, 404)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.statut, 'confirmed')

    def test_proprietaire_peut_enregistrer_un_paiement_especes_recu(self):
        self.reservation.paye = False
        self.reservation.save(update_fields=['paye'])
        paiement = Paiement.objects.create(
            reservation=self.reservation,
            montant=self.reservation.montant_final,
            methode='cash',
            statut='pending',
        )
        payments_page = self.client.get(reverse('logement:mes_paiements'))
        self.assertContains(payments_page, 'Confirmer le paiement reçu')

        response = self.client.post(
            reverse('logement:confirmer_paiement_especes', args=[paiement.pk]),
        )

        self.assertRedirects(response, reverse('logement:mes_paiements'))
        paiement.refresh_from_db()
        self.reservation.refresh_from_db()
        self.assertEqual(paiement.statut, 'completed')
        self.assertIsNotNone(paiement.completed_at)
        self.assertTrue(self.reservation.paye)
        self.assertNotContains(
            self.client.get(reverse('logement:mes_paiements')),
            'Confirmer le paiement reçu',
        )

    def test_arrivee_ne_peut_pas_etre_enregistree_hors_dates_du_sejour(self):
        today = timezone.localdate()
        self.reservation.date_arrivee = today + timedelta(days=2)
        self.reservation.date_depart = today + timedelta(days=3)
        self.reservation.save(update_fields=['date_arrivee', 'date_depart', 'updated_at'])

        response = self.client.post(
            reverse('logement:changer_statut_reservation', args=[self.reservation.pk]),
            {'action': 'check_in'},
        )

        self.assertRedirects(response, reverse('logement:mes_reservations'))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.statut, 'confirmed')


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

    def test_calendrier_garde_une_chambre_occupee_pendant_le_sejour(self):
        checked_in = self.create_reservation(
            'Client En Séjour',
            '2026-10-10',
            '2026-10-12',
            1,
            'checked_in',
        )
        checked_in.unites.set(self.logement.unites.filter(numero='1'))

        response = self.client.get(
            reverse('logement:calendrier_reservations'),
            {'year': 2026, 'month': 10, 'logement': self.logement.id},
        )

        self.assertEqual(response.status_code, 200)
        days = {day['number']: day for day in response.context['days'] if day}
        self.assertEqual(days[10]['reserved_units'], 1)
        self.assertEqual(days[10]['available_units'], 2)
        self.assertEqual(days[10]['label'], 'En séjour')
        self.assertContains(response, 'Client En Séjour')


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
    def test_accueil_ne_charge_que_les_annonces_de_la_page_demandee(self):
        for index in range(13):
            Logement.objects.create(
                titre=f'Annonce {index}',
                description='Description test',
                ville='Abidjan',
                account_type='individu',
            )

        first_page = self.client.get(reverse('logement:home'))
        second_page = self.client.get(reverse('logement:home'), {'page': '2'})

        self.assertEqual(len(first_page.context['annonces']), 12)
        self.assertEqual(first_page.context['total_annonces'], 13)
        self.assertEqual(len(second_page.context['annonces']), 1)
        self.assertEqual(second_page.context['page_obj'].number, 2)

    def test_liste_tous_types_limite_chaque_categorie_a_une_page(self):
        for index in range(13):
            Logement.objects.create(
                titre=f'Hôtel {index}',
                description='Description test',
                ville='Abidjan',
                account_type='hotel',
            )

        first_page = self.client.get(reverse('logement:listings_all_types'))
        second_page = self.client.get(
            reverse('logement:listings_all_types'),
            {'hotel_page': '2'},
        )

        self.assertEqual(len(first_page.context['hotels']), 12)
        self.assertEqual(first_page.context['hotel_count'], 13)
        self.assertEqual(len(second_page.context['hotels']), 1)
        self.assertEqual(second_page.context['hotel_page'].number, 2)

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
