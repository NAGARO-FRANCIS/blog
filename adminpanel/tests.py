import io
import tempfile
from unittest import mock

from django.contrib import admin
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.admin import DocumentVerificationAdmin
from accounts.models import (
    DocumentVerification,
    Notification,
    Profile,
    ProfessionalProfile,
    VerificationLog,
)
from colocation.models import ColocationAnnonce
from logement.models import AvisLogement, Etablissement, Logement, Paiement, Reservation, SignalementAvis


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

    def test_users_filter_supports_the_five_account_categories(self):
        profiles = {'locataire': self.profile}
        for username, category in (
            ('hotel_account', 'hotel'),
            ('residence_account', 'residence'),
            ('owner_account', 'proprietaire'),
            ('tourist_account', 'touriste'),
        ):
            user = User.objects.create_user(username=username, password='StrongPass123!')
            profile = user.profile
            if category in {'hotel', 'residence'}:
                profile.account_type = category
            else:
                profile.account_type = 'individu'
                profile.role = category
            profile.save(update_fields=['account_type', 'role'])
            profiles[category] = profile

        self.client.force_login(self.admin)
        for category, profile in profiles.items():
            with self.subTest(category=category):
                response = self.client.get(
                    reverse('adminpanel:users'),
                    {'account_type': category},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['page_obj'].paginator.count, 1)
                self.assertEqual(response.context['users'][0].pk, profile.user_id)

    def test_management_sections_display_their_records(self):
        avis, signalement = self.create_review_and_report()
        Paiement.objects.create(
            reservation=avis.reservation,
            montant=30000,
            methode='mobile_money',
            statut='completed',
        )
        owner = User.objects.create_user(username='colocation_owner', password='StrongPass123!')
        ColocationAnnonce.objects.create(
            proprietaire=owner,
            ville='Abidjan',
            quartier='Cocody',
            budget_mensuel=150000,
            description='Annonce de colocation visible dans le panneau admin.',
        )
        Logement.objects.create(
            titre='Recherche de colocataire par un locataire',
            description='Annonce logement publiée par un locataire.',
            ville='Abidjan',
            account_type='individu',
            proprietaire=owner,
        )
        self.client.force_login(self.admin)

        sections = (
            ('adminpanel:logements', 'Appartement à Abidjan'),
            ('adminpanel:colocations', 'Annonce de colocation visible dans le panneau admin.'),
            ('adminpanel:reservations', 'Client test'),
            ('adminpanel:finance', 'Appartement à Abidjan'),
            ('adminpanel:avis', 'Avis à modérer'),
            ('adminpanel:signalements', 'Contenu inapproprié'),
            ('adminpanel:notifications', 'Nouvelle alerte admin'),
        )
        for route_name, visible_content in sections:
            with self.subTest(section=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, visible_content)

        tenant_ads = self.client.get(
            reverse('adminpanel:colocations'),
            {'role': 'locataire'},
        )
        self.assertEqual(tenant_ads.status_code, 200)
        self.assertContains(tenant_ads, 'Recherche un colocataire')
        self.assertContains(tenant_ads, 'Recherche de colocataire par un locataire')
        self.assertEqual(tenant_ads.context['locataires_recherche'], 2)
        self.assertEqual(len(tenant_ads.context['items']), 1)
        self.assertEqual(len(tenant_ads.context['logement_items']), 1)

        self.assertContains(self.client.get(reverse('adminpanel:avis')), 'Masquer')
        self.assertContains(self.client.get(reverse('adminpanel:signalements')), 'Marquer traité')

    def test_logements_section_paginates_all_records(self):
        owner = User.objects.create_user(username='many_listings_owner', password='StrongPass123!')
        Logement.objects.bulk_create([
            Logement(
                titre=f'Logement admin {index}',
                description='Description de test',
                ville='Abidjan',
                proprietaire=owner,
            )
            for index in range(27)
        ])
        self.client.force_login(self.admin)

        first_page = self.client.get(reverse('adminpanel:logements'))
        second_page = self.client.get(reverse('adminpanel:logements'), {'page': 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.context['page_obj'].paginator.count, 27)
        self.assertEqual(len(first_page.context['items']), 25)
        self.assertContains(first_page, 'Page 1 / 2')
        self.assertContains(second_page, 'Page 2 / 2')
        self.assertEqual(len(second_page.context['items']), 2)

    def create_review_and_report(self):
        owner = User.objects.create_user(username='owner_reviews', password='StrongPass123!')
        reviewer = User.objects.create_user(username='reviewer', password='StrongPass123!')
        logement = Logement.objects.create(
            titre='Appartement à Abidjan',
            description='Logement de test',
            ville='Abidjan',
            account_type='hotel',
            prix_par_nuit=10000,
            proprietaire=owner,
        )
        reservation = Reservation.objects.create(
            logement=logement,
            client_user=reviewer,
            client_nom='Client test',
            client_email='client@example.com',
            client_telephone='+2250700000000',
            date_arrivee='2026-09-07',
            date_depart='2026-09-10',
            nombre_personnes=1,
            nombre_chambres=1,
            prix_par_nuit=10000,
            nombre_nuits=3,
            prix_total=30000,
            montant_final=30000,
            statut='completed',
        )
        avis = AvisLogement.objects.create(
            logement=logement,
            reservation=reservation,
            auteur=reviewer,
            note_logement=2,
            commentaire='Avis à modérer',
        )
        signalement = SignalementAvis.objects.create(
            avis=avis,
            auteur=owner,
            motif='Contenu inapproprié',
        )
        return avis, signalement

    def create_verification_applicant(self):
        user = User.objects.create_user(
            username='verification_applicant',
            email='applicant@example.com',
            password='StrongPass123!',
        )
        profile = user.profile
        profile.verification_status = 'pending'
        profile.save(update_fields=['verification_status'])
        DocumentVerification.objects.create(
            profile=profile,
            document_type='id_front',
            document_file=SimpleUploadedFile('applicant-front.jpg', b'fake-image', content_type='image/jpeg'),
            status='pending',
        )
        return profile

    def test_reviews_section_can_hide_and_restore_a_review(self):
        avis, _ = self.create_review_and_report()
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:avis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avis à modérer')
        self.assertContains(response, 'Masquer')

        response = self.client.post(
            reverse('adminpanel:toggle_avis_visibility', args=[avis.id])
        )
        self.assertRedirects(response, reverse('adminpanel:avis'))
        avis.refresh_from_db()
        self.assertFalse(avis.est_visible)

        response = self.client.post(
            reverse('adminpanel:toggle_avis_visibility', args=[avis.id])
        )
        self.assertRedirects(response, reverse('adminpanel:avis'))
        avis.refresh_from_db()
        self.assertTrue(avis.est_visible)

    def test_reports_section_can_mark_a_report_as_treated(self):
        _, signalement = self.create_review_and_report()
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:signalements'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contenu inapproprié')
        self.assertContains(response, 'Marquer traité')

        response = self.client.post(
            reverse('adminpanel:traiter_signalement', args=[signalement.id])
        )
        self.assertRedirects(response, reverse('adminpanel:signalements'))
        signalement.refresh_from_db()
        self.assertTrue(signalement.traite)

    def test_document_approval_waits_until_all_three_required_documents_are_uploaded(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:approve_document', args=[document.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        self.assertContains(response, '3 pièces doivent être téléversées')
        self.assertContains(response, '1/3 reçues')
        document.refresh_from_db()
        self.assertEqual(document.status, 'pending')
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.verified)
        self.assertEqual(self.profile.verification_status, 'pending')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_profile_is_verified_only_after_all_three_uploaded_documents_are_approved_and_notified(self):
        front = DocumentVerification.objects.get(profile=self.profile)
        back = DocumentVerification.objects.create(
            profile=self.profile,
            document_type='id_back',
            document_file=SimpleUploadedFile('back.jpg', b'fake-image', content_type='image/jpeg'),
            status='pending',
        )
        selfie = DocumentVerification.objects.create(
            profile=self.profile,
            document_type='selfie',
            document_file=SimpleUploadedFile('selfie.jpg', b'fake-image', content_type='image/jpeg'),
            status='pending',
        )
        self.client.force_login(self.admin)

        for document in (front, back):
            response = self.client.post(
                reverse('adminpanel:approve_document', args=[document.pk])
            )
            self.assertRedirects(
                response,
                reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
            )
            self.profile.refresh_from_db()
            self.assertFalse(self.profile.verified)
            self.assertEqual(self.profile.verification_status, 'pending')

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.admin,
                title='Identité vérifiée',
            ).exists()
        )
        self.assertEqual(mail.outbox, [])

        response = self.client.post(
            reverse('adminpanel:approve_document', args=[selfie.pk])
        )
        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.verified)
        self.assertEqual(self.profile.verification_status, 'verified')
        self.assertTrue(self.profile.can_publish)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.admin,
                title='Identité vérifiée',
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('trois pièces d’identité ont été vérifiées', mail.outbox[0].body)

    def test_verification_queue_shows_upload_count_and_waits_for_all_three_files(self):
        applicant = self.create_verification_applicant()
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:verifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1/3 reçues')
        self.assertContains(response, 'Ouvrir le dossier')
        self.assertEqual(len(response.context['items']), 1)
        self.assertEqual(response.context['items'][0].pk, applicant.pk)

    def test_staff_can_open_a_grouped_dossier_with_all_document_types(self):
        applicant = self.create_verification_applicant()
        for document_type, filename in (
            ('id_back', 'back.jpg'),
            ('selfie', 'selfie.jpg'),
        ):
            DocumentVerification.objects.create(
                profile=applicant,
                document_type=document_type,
                document_file=SimpleUploadedFile(filename, b'fake-image', content_type='image/jpeg'),
                status='pending',
            )
        self.client.force_login(self.admin)

        queue_response = self.client.get(reverse('adminpanel:verifications'))
        response = self.client.get(
            reverse('adminpanel:verification_dossier', args=[applicant.pk])
        )

        self.assertEqual(len(queue_response.context['items']), 1)
        self.assertEqual(queue_response.context['items'][0].pk, applicant.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avant')
        self.assertContains(response, 'Arrière')
        self.assertContains(response, 'Selfie avec pièce')
        self.assertContains(response, 'Approuver cette pièce')
        self.assertContains(response, 'Téléphone')
        self.assertContains(response, 'Rejeter cette pièce')
        self.assertContains(response, 'Marquer à revoir')

    def test_staff_can_review_complete_professional_file_from_identity_dossier(self):
        applicant = self.create_verification_applicant()
        applicant.account_type = 'hotel'
        applicant.role = 'proprietaire'
        applicant.verified = True
        applicant.verification_status = 'verified'
        applicant.save(update_fields=['account_type', 'role', 'verified', 'verification_status'])
        applicant.documents.all().delete()
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=applicant,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )
        professional_profile = ProfessionalProfile.objects.create(
            profile=applicant,
            establishment_type='hotel',
            establishment_name='Hôtel Ivoire',
            siret_or_rccm='CI-HOTEL-REVIEW',
            legal_representative='Responsable Ivoire',
            legal_phone='+2250700000000',
            establishment_address='Rue des Jardins',
            establishment_city='Abidjan',
            establishment_postal_code='01 BP',
            establishment_country='Côte d’Ivoire',
            number_of_rooms=12,
            number_of_floors=3,
            website='https://hotel.example.com',
            wifi=True,
            parking=True,
            legal_document='legal/review.pdf',
            establishment_photo='photos/review.jpg',
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('adminpanel:verification_dossier', args=[applicant.pk])
        )
        queue_response = self.client.get(reverse('adminpanel:verifications'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [profile.pk for profile in queue_response.context['items']],
            [applicant.pk],
        )
        self.assertContains(response, 'RCCM / SIRET')
        self.assertContains(response, 'Hôtel Ivoire')
        self.assertContains(response, 'Responsable Ivoire')
        self.assertContains(response, 'Approuver l’établissement')
        self.assertContains(
            response,
            reverse('adminpanel:verification_establishment_document_file', args=[
                applicant.pk,
                'legal_document',
            ]),
        )
        self.assertFalse(professional_profile.is_verified)

        response = self.client.post(
            reverse('adminpanel:approve_professional_profile', args=[applicant.pk])
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[applicant.pk]),
        )
        professional_profile.refresh_from_db()
        self.assertTrue(professional_profile.is_verified)
        review_queue = self.client.get(reverse('adminpanel:hotels_residences'))
        self.assertEqual(review_queue.context['items'].paginator.count, 0)
        verified_list = self.client.get(
            reverse('adminpanel:hotels_residences'),
            {'statut': 'verified'},
        )
        self.assertEqual(
            [item.pk for item in verified_list.context['items']],
            [professional_profile.pk],
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_staff_can_reject_a_pending_registration_from_its_dossier(self):
        applicant = self.create_verification_applicant()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:reject_profile', args=[applicant.pk]),
            {'rejection_reason': 'Les justificatifs ne correspondent pas aux informations déclarées.'},
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[applicant.pk]),
        )
        applicant.refresh_from_db()
        applicant.user.refresh_from_db()
        self.assertEqual(applicant.verification_status, 'rejected')
        self.assertFalse(applicant.user.is_active)
        self.assertTrue(
            VerificationLog.objects.filter(
                profile=applicant,
                action='profile_rejected',
                performed_by=self.admin,
            ).exists()
        )

    def test_staff_can_flag_document_with_a_required_review_note(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:flag_document', args=[document.pk]),
            {'admin_notes': 'La photo est floue.'},
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        document.refresh_from_db()
        self.assertEqual(document.status, 'flagged')
        self.assertEqual(document.admin_notes, 'La photo est floue.')

    def test_verification_document_file_is_available_only_to_staff(self):
        image_bytes = io.BytesIO()
        Image.new('RGB', (10, 10), color=(30, 80, 140)).save(image_bytes, format='JPEG')
        document = DocumentVerification.objects.get(profile=self.profile)

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            document.document_file.save(
                'identity.jpg',
                SimpleUploadedFile('identity.jpg', image_bytes.getvalue(), content_type='image/jpeg'),
                save=True,
            )

            response = self.client.get(
                reverse('adminpanel:verification_document_file', args=[document.pk])
            )
            self.assertEqual(response.status_code, 302)

            self.client.force_login(self.admin)
            response = self.client.get(
                reverse('adminpanel:verification_document_file', args=[document.pk])
            )
            response_body = b''.join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response_body, image_bytes.getvalue())

    def create_verified_professional_establishment(self):
        self.profile.account_type = 'residence'
        self.profile.role = 'proprietaire'
        self.profile.verification_status = 'verified'
        self.profile.verified = True
        self.profile.save(update_fields=[
            'account_type',
            'role',
            'verification_status',
            'verified',
        ])
        self.profile.documents.all().delete()
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=self.profile,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )
        professional_profile = ProfessionalProfile.objects.create(
            profile=self.profile,
            establishment_type='residence',
            establishment_name='Résidence test',
            siret_or_rccm='CI-TEST-RESIDENCE',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=4,
            legal_document='legal/test.pdf',
            establishment_photo='facade/test.jpg',
        )
        establishment = Etablissement.objects.create(
            proprietaire=self.admin,
            nom='Résidence test',
            type_etablissement='residence',
            ville='Abidjan',
        )
        return professional_profile, establishment

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_staff_can_review_and_approve_establishment_to_unlock_publication(self):
        professional_profile, establishment = self.create_verified_professional_establishment()
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.verified)
        self.assertEqual(self.profile.verification_status, 'verified')
        self.assertTrue(self.profile.has_verified_identity_documents)
        self.client.force_login(self.admin)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.verified)

        list_response = self.client.get(reverse('adminpanel:hotels_residences'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            [item.pk for item in list_response.context['items']],
            [professional_profile.pk],
        )
        self.assertContains(list_response, 'Résidence test')
        self.assertContains(list_response, 'Examiner le dossier')
        self.assertContains(
            list_response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        self.assertEqual(list_response.context['eligible_establishments'], 1)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.verified)

        review_response = self.client.get(
            reverse('adminpanel:establishment_review', args=[establishment.pk]),
            follow=True,
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertRedirects(
            review_response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        self.assertTrue(review_response.context['verification_profile'].verified)
        self.assertTrue(
            review_response.context['verification_profile'].has_verified_identity_documents
        )
        self.assertFalse(review_response.context['professional_profile'].is_verified)
        self.assertTrue(review_response.context['professional_profile'].legal_document)
        self.assertTrue(review_response.context['professional_profile'].establishment_photo)
        self.assertContains(review_response, 'CI-TEST-RESIDENCE')
        self.assertContains(review_response, 'Ouvrir le document PDF')
        self.assertContains(review_response, 'Approuver l’établissement')
        self.assertFalse(self.profile.can_publish)

        response = self.client.post(
            reverse('adminpanel:approve_establishment', args=[establishment.pk]),
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        professional_profile.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertTrue(professional_profile.is_verified)
        self.assertTrue(professional_profile.verification_date)
        self.assertTrue(self.profile.can_publish)
        self.assertTrue(
            VerificationLog.objects.filter(
                profile=self.profile,
                action='establishment_verified',
                performed_by=self.admin,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.admin,
                title='Établissement vérifié',
            ).exists()
        )

    def test_establishment_cannot_be_approved_before_identity_is_verified(self):
        self.profile.account_type = 'residence'
        self.profile.save(update_fields=['account_type'])
        professional_profile = ProfessionalProfile.objects.create(
            profile=self.profile,
            establishment_type='residence',
            establishment_name='Résidence en attente',
            siret_or_rccm='CI-TEST-PENDING',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=2,
            legal_document='legal/test.pdf',
            establishment_photo='facade/test.jpg',
        )
        establishment = Etablissement.objects.create(
            proprietaire=self.admin,
            nom='Résidence en attente',
            type_etablissement='residence',
            ville='Abidjan',
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:approve_establishment', args=[establishment.pk]),
            follow=True,
        )

        self.assertContains(response, 'Vérifiez d’abord l’identité du gestionnaire')
        professional_profile.refresh_from_db()
        self.assertFalse(professional_profile.is_verified)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_staff_can_automatically_approve_all_complete_establishments_without_existing_listings(self):
        eligible_user = User.objects.create_user(
            username='eligible_hotel_owner',
            email='eligible.hotel@example.com',
            password='StrongPass123!',
        )
        eligible_profile = eligible_user.profile
        eligible_profile.account_type = 'hotel'
        eligible_profile.verified = True
        eligible_profile.verification_status = 'verified'
        eligible_profile.save(update_fields=['account_type', 'verified', 'verification_status'])
        eligible_professional_profile = ProfessionalProfile.objects.create(
            profile=eligible_profile,
            establishment_type='hotel',
            establishment_name='Hôtel éligible',
            siret_or_rccm='CI-AUTO-ELIGIBLE',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=3,
            legal_document='legal/eligible.pdf',
            establishment_photo='facade/eligible.jpg',
        )
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=eligible_profile,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )

        incomplete_user = User.objects.create_user(
            username='incomplete_hotel_owner',
            email='incomplete.hotel@example.com',
            password='StrongPass123!',
        )
        incomplete_profile = incomplete_user.profile
        incomplete_profile.account_type = 'hotel'
        incomplete_profile.verified = True
        incomplete_profile.verification_status = 'verified'
        incomplete_profile.save(update_fields=['account_type', 'verified', 'verification_status'])
        incomplete_professional_profile = ProfessionalProfile.objects.create(
            profile=incomplete_profile,
            establishment_type='hotel',
            establishment_name='Hôtel incomplet',
            siret_or_rccm='CI-AUTO-INCOMPLETE',
            legal_representative='Responsable test',
            legal_phone='+22501020304',
            establishment_address='Adresse test',
            establishment_city='Abidjan',
            number_of_rooms=2,
            legal_document='legal/incomplete.pdf',
            establishment_photo='facade/incomplete.jpg',
        )
        for document_type in ('id_front', 'id_back'):
            DocumentVerification.objects.create(
                profile=incomplete_profile,
                document_type=document_type,
                document_file=f'identity/{document_type}.jpg',
                status='verified',
            )

        self.client.force_login(self.admin)
        list_response = self.client.get(reverse('adminpanel:hotels_residences'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Hôtel éligible')
        self.assertEqual(list_response.context['eligible_establishments'], 1)

        response = self.client.post(
            reverse('adminpanel:approve_eligible_establishments'),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 établissement(s) éligible(s) approuvé(s)')
        eligible_professional_profile.refresh_from_db()
        incomplete_professional_profile.refresh_from_db()
        self.assertTrue(eligible_professional_profile.is_verified)
        self.assertTrue(eligible_professional_profile.verification_date)
        self.assertFalse(incomplete_professional_profile.is_verified)
        self.assertTrue(
            VerificationLog.objects.filter(
                profile=eligible_profile,
                action='establishment_verified',
                performed_by=self.admin,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=eligible_user,
                title='Établissement vérifié',
            ).exists()
        )
        self.assertTrue(eligible_profile.can_publish)

    def test_establishment_documents_are_restricted_to_staff(self):
        _, establishment = self.create_verified_professional_establishment()
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            professional_profile = self.profile.professional_profile
            professional_profile.legal_document.save(
                'registry.pdf',
                SimpleUploadedFile('registry.pdf', b'%PDF-1.4 test', content_type='application/pdf'),
                save=True,
            )

            response = self.client.get(
                reverse(
                    'adminpanel:establishment_document_file',
                    args=[establishment.pk, 'legal_document'],
                )
            )
            self.assertEqual(response.status_code, 302)

            self.client.force_login(self.admin)
            response = self.client.get(
                reverse(
                    'adminpanel:establishment_document_file',
                    args=[establishment.pk, 'legal_document'],
                )
            )
            response_body = b''.join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'].split(';')[0], 'attachment')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response_body, b'%PDF-1.4 test')

    def test_django_admin_bulk_approval_also_waits_for_all_three_uploads(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        request = RequestFactory().post('/admin/accounts/documentverification/')
        request.user = self.admin
        model_admin = DocumentVerificationAdmin(DocumentVerification, admin.site)

        with mock.patch.object(model_admin, 'message_user') as message_user:
            model_admin.approve_documents(
                request,
                DocumentVerification.objects.filter(pk=document.pk),
            )

        document.refresh_from_db()
        self.assertEqual(document.status, 'pending')
        message_user.assert_called_once()
        self.assertIn('3 pièces doivent être téléversées', message_user.call_args.args[1])

    def test_pending_document_can_be_rejected_by_post(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:reject_document', args=[document.id])
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[self.profile.pk]),
        )
        document.refresh_from_db()
        self.assertEqual(document.status, 'rejected')
        self.assertEqual(document.rejection_reason, 'Document non conforme')

    def test_document_moderation_rejects_get_requests(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('adminpanel:approve_document', args=[document.id])
        )

        self.assertEqual(response.status_code, 405)

    def test_staff_can_activate_account_without_approving_identity_documents(self):
        user = User.objects.create_user(
            username='amani_joas_test',
            first_name='AMANI',
            last_name='JOAS',
            password='StrongPass123!',
            is_active=False,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:activate_user', args=[user.pk]),
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:verification_dossier', args=[user.profile.pk]),
        )
        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(user.profile.email_verified)
        self.assertFalse(user.profile.phone_verified)
        self.assertFalse(user.profile.verified)
        self.assertEqual(user.profile.verification_status, 'pending')
        self.assertTrue(
            VerificationLog.objects.filter(
                profile=user.profile,
                action='account_activated',
                performed_by=self.admin,
            ).exists()
        )

        self.client.logout()
        self.assertTrue(self.client.login(username='amani_joas_test', password='StrongPass123!'))

    def test_users_control_panel_shows_activation_action_for_inactive_accounts(self):
        user = User.objects.create_user(
            username='inactive_user_in_control_panel',
            first_name='Amani',
            last_name='Joas',
            password='StrongPass123!',
            is_active=False,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:users'), {'q': 'Joas'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amani Joas')
        self.assertContains(
            response,
            reverse('adminpanel:activate_user', args=[user.pk]),
        )

    def test_users_control_panel_filters_flagged_identities(self):
        flagged_user = User.objects.create_user(
            username='flagged_user_in_control_panel',
            first_name='Awa',
            last_name='Kone',
            password='StrongPass123!',
        )
        flagged_user.profile.verification_status = 'flagged'
        flagged_user.profile.save(update_fields=['verification_status'])
        other_user = User.objects.create_user(
            username='verified_user_in_control_panel',
            first_name='Mariam',
            last_name='Traore',
            password='StrongPass123!',
        )
        other_user.profile.verification_status = 'verified'
        other_user.profile.save(update_fields=['verification_status'])
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:users'), {'status': 'flagged'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'flagged_user_in_control_panel')
        self.assertNotContains(response, 'verified_user_in_control_panel')
        self.assertContains(response, 'À revoir')
        self.assertContains(response, 'Affichage de 1 à 1 sur 1 utilisateur(s)')

    def test_section_navigation_highlights_the_open_section(self):
        self.client.force_login(self.admin)
        users_url = reverse('adminpanel:users')

        for route_name in ('finance', 'verifications'):
            with self.subTest(section=route_name):
                response = self.client.get(reverse(f'adminpanel:{route_name}'))
                current_url = reverse(f'adminpanel:{route_name}')

                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f'href="{current_url}" class="active" aria-current="page"',
                )
                self.assertNotContains(
                    response,
                    f'href="{users_url}" class="active" aria-current="page"',
                )

        response = self.client.get(reverse('adminpanel:hotels_residences'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_section'], 'hotels_residences')

    def test_non_staff_cannot_activate_accounts(self):
        user = User.objects.create_user(
            username='user_to_activate',
            password='StrongPass123!',
            is_active=False,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('adminpanel:activate_user', args=[user.pk]),
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_account_activation_rejects_get_requests(self):
        user = User.objects.create_user(
            username='get_activation_user',
            password='StrongPass123!',
            is_active=False,
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('adminpanel:activate_user', args=[user.pk]),
        )

        self.assertEqual(response.status_code, 405)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
