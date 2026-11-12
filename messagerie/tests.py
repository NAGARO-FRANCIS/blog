from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import DocumentVerification
from ivoire.context_processors import unread_messages_count
from logement.models import Logement
from .models import Conversation, Message, ParticipationConversation


class MessagerieTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='pass1234')
        self.user2 = User.objects.create_user(username='bob', password='pass1234')
        self.verify_identity(self.user1)
        self.verify_identity(self.user2)

    def verify_identity(self, user):
        profile = user.profile
        profile.verification_status = 'verified'
        profile.verified = True
        profile.save(update_fields=['verification_status', 'verified'])
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=profile,
                document_type=document_type,
                document_file=f'identity/{user.username}_{document_type}.jpg',
                status='verified',
            )

    def test_unread_message_count_uses_one_query_and_ignores_hidden_conversations(self):
        visible_conversation = Conversation.objects.create()
        visible_conversation.participants.add(self.user1, self.user2)
        hidden_conversation = Conversation.objects.create()
        hidden_conversation.participants.add(self.user1, self.user2)
        ParticipationConversation.objects.filter(
            conversation=hidden_conversation,
            user=self.user1,
        ).update(masquee=True)
        Message.objects.create(
            conversation=visible_conversation,
            expediteur=self.user2,
            contenu='Message non lu',
        )
        Message.objects.create(
            conversation=visible_conversation,
            expediteur=self.user1,
            contenu='Mon message',
        )
        Message.objects.create(
            conversation=hidden_conversation,
            expediteur=self.user2,
            contenu='Message dans une conversation masquée',
        )
        request = RequestFactory().get('/')
        request.user = self.user1

        with self.assertNumQueries(1):
            result = unread_messages_count(request)

        self.assertEqual(result['unread_messages_count'], 1)

    def test_send_message_with_audio_attachment_saves_file(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        attachment = SimpleUploadedFile(
            'voice.ogg',
            b'audio-bytes',
            content_type='audio/ogg',
        )

        response = self.client.post(
            reverse('messagerie:envoyer_message'),
            {
                'conversation_id': conversation.id,
                'contenu': 'Bonjour Bob',
                'attachment': attachment,
            },
        )

        self.assertEqual(response.status_code, 302)
        message = Message.objects.get(conversation=conversation, expediteur=self.user1)
        self.assertEqual(message.contenu, 'Bonjour Bob')
        self.assertTrue(message.attachment)
        self.assertEqual(message.message_type, 'audio')

    def test_unverified_user_cannot_send_message(self):
        unverified_user = User.objects.create_user(
            username='unverified_sender',
            password='pass1234',
        )
        for document_type in ('id_front', 'id_back', 'selfie'):
            DocumentVerification.objects.create(
                profile=unverified_user.profile,
                document_type=document_type,
                document_file=f'identity/pending_{document_type}.jpg',
                status='pending',
            )
        conversation = Conversation.objects.create()
        conversation.participants.add(unverified_user, self.user2)
        self.client.force_login(unverified_user)

        response = self.client.post(
            reverse('messagerie:envoyer_message'),
            {'conversation_id': conversation.id, 'contenu': 'Bonjour'},
        )

        self.assertRedirects(response, reverse('accounts:verification_docs'))
        self.assertFalse(Message.objects.filter(conversation=conversation).exists())

    def test_unverified_user_cannot_start_conversation(self):
        unverified_user = User.objects.create_user(
            username='unverified_conversation_starter',
            password='pass1234',
        )
        self.client.force_login(unverified_user)

        response = self.client.get(
            reverse('messagerie:demarrer_conversation', args=[self.user2.id])
        )

        self.assertRedirects(response, reverse('accounts:verification_docs'))
        self.assertFalse(
            Conversation.objects.filter(participants=unverified_user).exists()
        )

    def test_send_message_with_webm_audio_attachment_is_classified_as_audio(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        attachment = SimpleUploadedFile(
            'voice-message.webm',
            b'audio-webm-bytes',
            content_type='audio/webm;codecs=opus',
        )

        response = self.client.post(
            reverse('messagerie:envoyer_message'),
            {
                'conversation_id': conversation.id,
                'contenu': '',
                'attachment': attachment,
            },
        )

        self.assertEqual(response.status_code, 302)
        message = Message.objects.get(conversation=conversation, expediteur=self.user1)
        self.assertEqual(message.message_type, 'audio')
        self.assertTrue(message.is_audio)

    def test_send_message_with_video_attachment_saves_file(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        attachment = SimpleUploadedFile(
            'visit.mp4',
            b'video-bytes',
            content_type='video/mp4',
        )

        response = self.client.post(
            reverse('messagerie:envoyer_message'),
            {
                'conversation_id': conversation.id,
                'contenu': '',
                'attachment': attachment,
            },
        )

        self.assertEqual(response.status_code, 302)
        message = Message.objects.get(conversation=conversation, expediteur=self.user1)
        self.assertEqual(message.message_type, 'video')
        self.assertTrue(message.is_video)

    def test_conversation_detail_renders_messages(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conversation, expediteur=self.user1, contenu='Salut !')

        response = self.client.get(reverse('messagerie:conversation_detail', args=[conversation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Salut !')

    def test_conversation_without_other_participant_renders_without_error(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1)

        response = self.client.get(
            reverse('messagerie:conversation_detail', args=[conversation.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact indisponible')
        self.assertContains(response, 'Le contact de cette conversation')
        self.assertContains(response, 'id="messageContent" disabled')

    def test_cannot_send_message_to_conversation_without_other_participant(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1)

        response = self.client.post(
            reverse('messagerie:envoyer_message'),
            {'conversation_id': conversation.id, 'contenu': 'Message sans destinataire'},
        )

        self.assertRedirects(
            response,
            reverse('messagerie:conversation_detail', args=[conversation.id]),
        )
        self.assertFalse(Message.objects.filter(conversation=conversation).exists())

    def test_conversation_list_uses_compact_openable_rows(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conversation, expediteur=self.user2, contenu='Bonjour Alice')

        response = self.client.get(reverse('messagerie:mes_conversations'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="conversation-item')
        self.assertContains(
            response,
            f'href="{reverse("messagerie:conversation_detail", args=[conversation.id])}"',
        )
        self.assertContains(response, 'Bonjour Alice')

    def test_conversation_list_handles_missing_other_participant(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1)

        response = self.client.get(reverse('messagerie:mes_conversations'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact indisponible')
        self.assertContains(response, 'avatar-placeholder">?</div>')

    def test_conversation_list_paginates_and_query_count_does_not_grow_per_conversation(self):
        self.client.login(username='alice', password='pass1234')
        for index in range(3):
            conversation = Conversation.objects.create()
            conversation.participants.add(self.user1, self.user2)
            Message.objects.create(
                conversation=conversation,
                expediteur=self.user2,
                contenu=f'Message {index}',
            )

        with CaptureQueriesContext(connection) as first_page_queries:
            response = self.client.get(reverse('messagerie:mes_conversations'))
        self.assertEqual(response.status_code, 200)
        first_query_count = len(first_page_queries)

        for index in range(3, 23):
            conversation = Conversation.objects.create()
            conversation.participants.add(self.user1, self.user2)
            Message.objects.create(
                conversation=conversation,
                expediteur=self.user2,
                contenu=f'Message {index}',
            )

        with CaptureQueriesContext(connection) as expanded_page_queries:
            expanded_response = self.client.get(reverse('messagerie:mes_conversations'))
        self.assertEqual(expanded_response.status_code, 200)
        self.assertEqual(len(expanded_page_queries), first_query_count)
        self.assertEqual(len(expanded_response.context['conversations']), 20)
        self.assertEqual(expanded_response.context['page_obj'].paginator.count, 23)

    def test_conversation_detail_displays_alternating_messages(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conversation, expediteur=self.user1, contenu='Bonjour')
        Message.objects.create(conversation=conversation, expediteur=self.user2, contenu='Salut')

        response = self.client.get(reverse('messagerie:conversation_detail', args=[conversation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'message-row sent')
        self.assertContains(response, 'message-row received')

    def test_send_message_from_logement_announcement_creates_conversation(self):
        owner = User.objects.create_user(username='owner', password='pass1234')
        logement = Logement.objects.create(
            titre='Belle maison',
            description='Maison spacieuse',
            ville='Abidjan',
            quartier='Cocody',
            prix=150000,
            proprietaire=owner,
            account_type='individu',
        )

        self.client.login(username='alice', password='pass1234')
        response = self.client.post(
            reverse('messagerie:envoyer_message_annonce', args=['logement', logement.id]),
            {'contenu': 'Bonjour, je suis intéressé par votre logement.'},
        )

        self.assertEqual(response.status_code, 302)
        conversation = Conversation.objects.filter(participants=self.user1).filter(participants=owner).first()
        self.assertIsNotNone(conversation)
        self.assertTrue(Message.objects.filter(conversation=conversation, expediteur=self.user1).exists())

    def test_detail_logement_uses_internal_message_link(self):
        owner = User.objects.create_user(username='owner', password='pass1234')
        logement = Logement.objects.create(
            titre='Belle maison',
            description='Maison spacieuse',
            ville='Abidjan',
            quartier='Cocody',
            prix=150000,
            proprietaire=owner,
            account_type='individu',
        )

        response = self.client.get(reverse('logement:detail_logement', args=[logement.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('messagerie:envoyer_message_annonce', args=['logement', logement.id])
        )
