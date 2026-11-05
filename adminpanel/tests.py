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
from logement.models import AvisLogement, Etablissement, Logement, Reservation, SignalementAvis


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
        self.client.force_login(self.admin)

        response = self.client.get(reverse('adminpanel:verifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1/3 pièces reçues')
        self.assertContains(response, 'Ouvrir le dossier')
        self.assertNotContains(response, 'Approuver')
        self.assertEqual(len(response.context['items']), 1)
        self.assertEqual(response.context['items'][0].pk, self.profile.pk)

    def test_staff_can_open_a_grouped_dossier_with_all_document_types(self):
        for document_type, filename in (
            ('id_back', 'back.jpg'),
            ('selfie', 'selfie.jpg'),
        ):
            DocumentVerification.objects.create(
                profile=self.profile,
                document_type=document_type,
                document_file=SimpleUploadedFile(filename, b'fake-image', content_type='image/jpeg'),
                status='pending',
            )
        self.client.force_login(self.admin)

        queue_response = self.client.get(reverse('adminpanel:verifications'))
        response = self.client.get(
            reverse('adminpanel:verification_dossier', args=[self.profile.pk])
        )

        self.assertEqual(len(queue_response.context['items']), 1)
        self.assertEqual(queue_response.context['items'][0].pk, self.profile.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avant')
        self.assertContains(response, 'Arrière')
        self.assertContains(response, 'Selfie avec pièce')
        self.assertContains(response, 'Approuver cette pièce')

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
        self.client.force_login(self.admin)

        list_response = self.client.get(reverse('adminpanel:hotels_residences'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Vérifier l’établissement')
        self.assertContains(list_response, 'Vérification en attente')
        self.assertContains(list_response, 'Établissements à vérifier')

        review_response = self.client.get(
            reverse('adminpanel:establishment_review', args=[establishment.pk])
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertTrue(review_response.context['identity_review_complete'])
        self.assertFalse(review_response.context['professional_profile'].is_verified)
        self.assertTrue(review_response.context['professional_profile'].legal_document)
        self.assertTrue(review_response.context['professional_profile'].establishment_photo)
        self.assertContains(review_response, 'CI-TEST-RESIDENCE')
        self.assertContains(review_response, 'Télécharger et examiner le document')
        self.assertContains(review_response, 'Approuver l’établissement et autoriser la publication')
        self.assertFalse(self.profile.can_publish)

        response = self.client.post(
            reverse('adminpanel:approve_establishment', args=[establishment.pk]),
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse('adminpanel:establishment_review', args=[establishment.pk]),
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

        self.assertRedirects(response, reverse('adminpanel:users'))
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
