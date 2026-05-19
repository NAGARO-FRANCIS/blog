from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('individu', 'Individu'),
        ('residence', 'Gestionnaire de Résidence'),
        ('hotel', 'Gestionnaire d\'Hôtel'),
    ]

    ROLE_CHOICES = [
        ('locataire', 'Locataire'),
        ('colocataire', 'Colocataire'),
        ('proprietaire', 'Propriétaire'),
    ]

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]

    PIECE_IDENTITE_CHOICES = [
        ('cni', 'Carte Nationale d\'Identité'),
        ('passport', 'Passeport'),
        ('permis', 'Permis de conduire'),
        ('carte_sejour', 'Carte de séjour'),
        ('carte_etudiant', 'Carte d\'étudiant'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('pending', '⏳ En attente de vérification'),
        ('verified', '✅ Vérifié'),
        ('rejected', '❌ Rejeté'),
        ('flagged', '⚠️ Signalé'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Type de compte
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='individu',
        help_text="Type de compte utilisateur"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='locataire')

    # Informations personnelles
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True)
    profession = models.CharField(max_length=120, blank=True)
    telephone = models.CharField(max_length=20)

    # Photo de profil
    photo_profil = models.ImageField(upload_to='profiles/', blank=True, null=True, help_text="Photo de profil")

    # Pièce d'identité
    type_piece_identite = models.CharField(
        max_length=20,
        choices=PIECE_IDENTITE_CHOICES,
        blank=True,
        help_text="Type de pièce d'identité"
    )
    numero_piece_identite = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Numéro de la pièce d'identité"
    )

    # Statut et vérification
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        help_text="Statut de vérification de l'inscription"
    )
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_connexion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f'Profil de {self.user.get_full_name() or self.user.username}'

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    def peut_publier_dans_ville(self, ville):
        """Vérifie si l'utilisateur peut publier dans une ville donnée"""
        return self.ville.lower().strip() == ville.lower().strip()

    @property
    def est_verifie(self):
        return self.verification_status == 'verified'

    @property
    def ville_residence(self):
        return self.ville

    def clean(self):
        from django.core.exceptions import ValidationError
        # Allow telephone to be empty for new profiles
        pass


class ProfessionalProfile(models.Model):
    """Profil étendu pour les gestionnaires de résidence et d'hôtel"""
    ESTABLISHMENT_TYPE_CHOICES = [
        ('residence', 'Résidence'),
        ('hotel', 'Hôtel'),
    ]

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_profile')
    
    # Informations de l'établissement
    establishment_type = models.CharField(
        max_length=20,
        choices=ESTABLISHMENT_TYPE_CHOICES,
        help_text="Type d'établissement"
    )
    establishment_name = models.CharField(
        max_length=200,
        help_text="Nom officiel de l'établissement"
    )
    
    # Détails légaux
    siret_or_rccm = models.CharField(
        max_length=50,
        unique=True,
        help_text="SIRET (France) ou RCCM (Côte d'Ivoire)"
    )
    legal_representative = models.CharField(
        max_length=150,
        help_text="Représentant légal de l'établissement"
    )
    legal_phone = models.CharField(
        max_length=20,
        help_text="Téléphone de contact légal"
    )
    
    # Adresse de l'établissement
    establishment_address = models.CharField(max_length=255)
    establishment_city = models.CharField(max_length=100)
    establishment_postal_code = models.CharField(max_length=10, blank=True)
    establishment_country = models.CharField(max_length=100, default='Côte d\'Ivoire')
    
    # Détails de l'établissement
    number_of_rooms = models.PositiveIntegerField(
        help_text="Nombre de chambres/unités"
    )
    number_of_floors = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Nombre d'étages"
    )
    website = models.URLField(blank=True, help_text="Site web de l'établissement")
    
    # Équipements
    wifi = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    restaurant = models.BooleanField(default=False)
    reception_24h = models.BooleanField(default=False, help_text="Réception 24h/24")
    air_conditioning = models.BooleanField(default=False)
    laundry_service = models.BooleanField(default=False)
    gym = models.BooleanField(default=False)
    conference_room = models.BooleanField(default=False)
    
    # Documents requis
    legal_document = models.FileField(
        upload_to='professional_docs/%Y/%m/',
        help_text="Document légal de constitution"
    )
    establishment_photo = models.ImageField(
        upload_to='professional_photos/%Y/%m/',
        help_text="Photo de façade de l'établissement"
    )
    
    # Statuts
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.establishment_name} ({self.get_establishment_type_display()})"


class DocumentVerification(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('id_front', 'Pièce d\'identité - Avant'),
        ('id_back', 'Pièce d\'identité - Arrière'),
        ('selfie', 'Selfie avec pièce d\'identité'),
        ('proof_address', 'Preuve de résidence'),
    ]

    STATUS_CHOICES = [
        ('pending', '⏳ En attente'),
        ('verified', '✅ Approuvé'),
        ('rejected', '❌ Rejeté'),
        ('flagged', '⚠️ À revoir'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(upload_to='verification_docs/%Y/%m/')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Métadonnées
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_documents')
    
    # Notes d'admin
    admin_notes = models.TextField(blank=True, help_text="Notes pour l'admin sur la vérification")
    rejection_reason = models.CharField(max_length=255, blank=True, help_text="Raison du rejet")
    
    # Sécurité
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 du fichier pour anti-fraude")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        unique_together = [('profile', 'document_type')]

    def __str__(self):
        return f"{self.profile.user.username} - {self.get_document_type_display()}"

    def is_complete_verification(self):
        """Vérifie si tous les documents requis sont présents"""
        required_docs = ['id_front', 'id_back', 'selfie']
        documents = self.profile.documents.filter(
            status='verified',
            document_type__in=required_docs
        ).values_list('document_type', flat=True)
        return set(documents) == set(required_docs)


class VerificationLog(models.Model):
    """Log de toutes les actions de vérification pour l'audit"""
    ACTION_CHOICES = [
        ('created', 'Inscription créée'),
        ('document_uploaded', 'Document téléchargé'),
        ('document_verified', 'Document approuvé'),
        ('document_rejected', 'Document rejeté'),
        ('profile_flagged', 'Profil signalé'),
        ('profile_verified', 'Profil vérifié'),
        ('profile_banned', 'Profil banni'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='verification_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.profile.user.username} - {self.get_action_display()}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            # Use get_or_create for safety
            Profile.objects.get_or_create(user=instance)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating profile for user {instance.id}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving profile for user {instance.id}: {str(e)}")


# ================================
# MODÈLES D'ABONNEMENT ET NOTIFICATIONS
# ================================

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
            self.read_at = models.DateTimeField.now()
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
