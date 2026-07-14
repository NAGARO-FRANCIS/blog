from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from logement.models import Logement
from .models import Conversation, Message


class MessagerieTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='pass1234')
        self.user2 = User.objects.create_user(username='bob', password='pass1234')

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

    def test_conversation_detail_renders_messages(self):
        self.client.login(username='alice', password='pass1234')
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conversation, expediteur=self.user1, contenu='Salut !')

        response = self.client.get(reverse('messagerie:conversation_detail', args=[conversation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Salut !')

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
