from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Conversation(models.Model):
    """Modèle pour les conversations entre utilisateurs"""
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        through='ParticipationConversation'
    )
    sujet = models.CharField(max_length=200, blank=True, help_text="Sujet de la conversation (optionnel)")
    annonce = models.ForeignKey(
        'colocation.ColocationAnnonce',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Annonce liée à la conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        participants_names = [p.username for p in self.participants.all()]
        return f"Conversation: {', '.join(participants_names)}"

    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation"""
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        """Retourne le dernier message de la conversation"""
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur"""
        return self.messages.filter(
            expediteur__in=self.participants.exclude(id=user.id),
            lu=False
        ).count()

    def mark_as_read(self, user):
        """Marque tous les messages comme lus pour un utilisateur"""
        self.messages.filter(
            expediteur__in=self.participants.exclude(id=user.id),
            lu=False
        ).update(lu=True)


class ParticipationConversation(models.Model):
    """Table de liaison pour les participants aux conversations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'conversation']

    def __str__(self):
        return f"{self.user.username} dans {self.conversation}"


class Message(models.Model):
    """Modèle pour les messages individuels"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,  # Temporaire pour migration
        blank=True
    )
    expediteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
    )
    contenu = models.TextField()
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Types de messages spéciaux
    MESSAGE_TYPES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
        ('system', 'Système'),
    ]
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text'
    )

    # Pour les pièces jointes
    attachment = models.FileField(
        upload_to='messages/%Y/%m/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message de {self.expediteur.username} à {self.created_at}'

    def clean(self):
        # Validation: un utilisateur ne peut pas s'envoyer de message à lui-même
        if self.expediteur == self.conversation.get_other_participant(self.expediteur):
            raise ValidationError("Vous ne pouvez pas vous envoyer de message à vous-même.")

    def save(self, *args, **kwargs):
        # Met à jour la date de dernière modification de la conversation
        super().save(*args, **kwargs)
        if self.conversation:
            self.conversation.updated_at = self.created_at
            self.conversation.save(update_fields=['updated_at'])

    @property
    def is_system_message(self):
        return self.message_type == 'system'

    @property
    def is_image(self):
        return self.message_type == 'image'

    @property
    def is_file(self):
        return self.message_type == 'file'


class MessageLu(models.Model):
    """Modèle pour tracker quels messages ont été lus par quels utilisateurs"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='lectures')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_lus')
    lu_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user.username} a lu le message {self.message.id}"
