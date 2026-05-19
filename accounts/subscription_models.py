from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    """Modèle pour gérer les abonnements entre utilisateurs (comme YouTube)"""
    
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text="Utilisateur qui s'abonne"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        help_text="Utilisateur dont on s'abonne"
    )
    
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notify_on_new_listing = models.BooleanField(
        default=True,
        help_text="Notifier quand cette personne publie une annonce"
    )
    
    class Meta:
        unique_together = [('subscriber', 'creator')]
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['subscriber', 'is_active']),
            models.Index(fields=['creator', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.subscriber.username} s'abonne à {self.creator.username}"
    
    @property
    def creator_name(self):
        return self.creator.profile.get_full_name() or self.creator.username
    
    @property
    def subscriber_count(self):
        """Nombre total d'abonnés du créateur"""
        return Subscription.objects.filter(creator=self.creator, is_active=True).count()


class Notification(models.Model):
    """Modèle pour gérer les notifications"""
    
    NOTIFICATION_TYPES = [
        ('new_listing', 'Nouvelle annonce'),
        ('subscription', 'Nouvel abonné'),
        ('message', 'Nouveau message'),
        ('reservation', 'Nouvelle réservation'),
        ('system', 'Notification système'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Utilisateur qui reçoit la notification"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    
    # Contenu
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Métadonnées
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_created',
        help_text="Utilisateur qui a déclenché la notification"
    )
    
    # Liens
    related_listing_id = models.PositiveIntegerField(null=True, blank=True)
    related_subscription_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Statut
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', '-created_at']),
        ]
    
    def __str__(self):
        return f"Notification pour {self.recipient.username}: {self.title}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def actor_name(self):
        if self.actor:
            return self.actor.profile.get_full_name() or self.actor.username
        return "Système"
    
    @classmethod
    def create_new_listing_notification(cls, subscriber, creator, listing):
        """Créer une notification pour une nouvelle annonce"""
        return cls.objects.create(
            recipient=subscriber,
            notification_type='new_listing',
            title=f"{creator.profile.get_full_name() or creator.username} a publié une annonce",
            message=f'Nouvelle annonce: "{listing.titre}"',
            actor=creator,
            related_listing_id=listing.id
        )
    
    @classmethod
    def create_subscription_notification(cls, subscriber, creator):
        """Créer une notification pour un nouvel abonné"""
        return cls.objects.create(
            recipient=creator,
            notification_type='subscription',
            title=f"Nouvel abonné",
            message=f"{subscriber.profile.get_full_name() or subscriber.username} s'est abonné à vous",
            actor=subscriber,
            related_subscription_id=subscriber.id
        )
