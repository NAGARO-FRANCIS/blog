from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import DocumentVerification, Notification, Profile
from logement.models import AvisLogement, Logement, Reservation, SignalementAvis


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

    def test_pending_document_can_be_approved_by_post(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:approve_document', args=[document.id])
        )

        self.assertRedirects(response, reverse('adminpanel:verifications'))
        document.refresh_from_db()
        self.assertEqual(document.status, 'verified')
        self.assertEqual(document.verified_by, self.admin)
        self.assertIsNotNone(document.verified_at)

    def test_pending_document_can_be_rejected_by_post(self):
        document = DocumentVerification.objects.get(profile=self.profile)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adminpanel:reject_document', args=[document.id])
        )

        self.assertRedirects(response, reverse('adminpanel:verifications'))
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
