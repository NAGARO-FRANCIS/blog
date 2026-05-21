from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Logement(models.Model):
    TYPE_LOGEMENT = [
        ('appartement', 'Appartement'),
        ('maison', 'Maison'),
        ('studio', 'Studio'),
        ('villa', 'Villa'),
        ('chambre', 'Chambre'),
    ]
    
    ACCOUNT_TYPE = [
        ('hotel', 'Hôtel'),
        ('residence', 'Résidence'),
        ('individu', 'Individu'),
    ]
    
    TYPE_CHARGE = [
        ('charges_comprises', 'Charges comprises'),
        ('charges_non_comprises', 'Charges non comprises'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Prix global (pour individu) - Voir prix_par_nuit ou prix_par_mois pour les professionnels"
    )
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    
    # Type de publication
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE,
        default='individu'
    )
    
    # Détails professionnels
    type_logement = models.CharField(max_length=20, choices=TYPE_LOGEMENT, default='appartement')
    surface = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    nombre_pieces = models.PositiveSmallIntegerField(default=1)
    nombre_chambres = models.PositiveSmallIntegerField(default=1)
    nombre_lits = models.PositiveSmallIntegerField(default=1, null=True, blank=True)
    capacite = models.PositiveSmallIntegerField(default=1, null=True, blank=True)
    nombre_salles_bain = models.PositiveSmallIntegerField(default=1)
    
    # Tarification flexible (hôtel par nuit, résidence par mois)
    prix_par_nuit = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    prix_par_mois = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Frais supplémentaires (hôtel)
    frais_nettoyage = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    min_sejour = models.PositiveSmallIntegerField(default=1, null=True, blank=True)
    
    # Conditions de bail (résidence)
    caution_mois = models.PositiveSmallIntegerField(default=2, null=True, blank=True)
    frais_agence = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    duree_min_bail = models.CharField(max_length=50, null=True, blank=True)
    type_charge = models.CharField(
        max_length=25,
        choices=TYPE_CHARGE,
        null=True, 
        blank=True
    )
    conditions_speciales = models.TextField(null=True, blank=True)
    
    # Équipements
    climatisation = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    garage = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    piscine = models.BooleanField(default=False)
    cuisine_equipee = models.BooleanField(default=False)
    
    # Équipements hôtel
    minibar = models.BooleanField(default=False)
    television = models.BooleanField(default=False)
    coffre_fort = models.BooleanField(default=False)
    reception_24h = models.BooleanField(default=False)
    restaurant = models.BooleanField(default=False)
    
    # Équipements résidence
    ascenseur = models.BooleanField(default=False)
    gardien = models.BooleanField(default=False)
    securite = models.BooleanField(default=False)
    buanderie = models.BooleanField(default=False)
    
    # Informations supplémentaires
    etage = models.PositiveSmallIntegerField(null=True, blank=True)
    meuble = models.BooleanField(default=False)
    disponible_depuis = models.DateField(null=True, blank=True)
    
    proprietaire = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.titre

    def get_nombre_photos(self):
        return self.photos.count()

    def get_nombre_videos(self):
        return self.videos.count()


class PhotoLogement(models.Model):
    logement = models.ForeignKey(
        Logement, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    image = models.ImageField(upload_to='logements/%Y/%m/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Photo de {self.logement.titre}"


class VideoLogement(models.Model):
    """Modèle pour les vidéos des logements"""
    logement = models.ForeignKey(
        Logement, 
        on_delete=models.CASCADE, 
        related_name='videos'
    )
    video = models.FileField(
        upload_to='logements/videos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Accepte les formats: MP4, WebM, Ogg (max 500 MB)"
    )
    titre = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0, blank=True)
    duree_secondes = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Vidéo: {self.titre or self.logement.titre}"


# ================================
# MODÈLES DE RÉSERVATION
# ================================

class DisponibiliteCalendrier(models.Model):
    """Gère les disponibilités et prix dynamiques par date"""
    STATUT_CHOICES = [
        ('disponible', '✅ Disponible'),
        ('occupe', '❌ Occupé'),
        ('bloquer', '🚫 Bloqué'),
    ]
    
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name='disponibilites'
    )
    date = models.DateField()
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='disponible'
    )
    prix_special = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Prix spécial pour cette date (si vide, utilise prix standard)"
    )
    
    class Meta:
        unique_together = ['logement', 'date']
        ordering = ['date']
        verbose_name_plural = "Disponibilités Calendrier"
    
    def __str__(self):
        return f"{self.logement.titre} - {self.date} ({self.get_statut_display()})"


class Reservation(models.Model):
    """Modèle pour les réservations (hôtels, résidences, touristes)"""
    STATUT_CHOICES = [
        ('pending', '⏳ En attente de paiement'),
        ('confirmed', '✅ Confirmée'),
        ('cancelled', '❌ Annulée'),
        ('completed', '✓ Complétée'),
    ]
    
    # Logement réservé
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    
    # Client: peut être un utilisateur enregistré ou un touriste anonyme
    client_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations'
    )
    
    # Informations touriste anonyme (si pas connecté)
    client_nom = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_telephone = models.CharField(max_length=20)
    
    # Dates et détails
    date_arrivee = models.DateField()
    date_depart = models.DateField()
    nombre_personnes = models.PositiveSmallIntegerField(default=1)
    nombre_chambres = models.PositiveSmallIntegerField(default=1, null=True, blank=True)
    
    # Remarques du client
    remarques = models.TextField(blank=True)
    
    # Tarification
    prix_par_nuit = models.DecimalField(max_digits=10, decimal_places=2)
    nombre_nuits = models.PositiveSmallIntegerField()
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Frais additionnels
    frais_service = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Frais de service/commission"
    )
    frais_nettoyage_reservation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True
    )
    montant_final = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statut et paiement
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending'
    )
    paye = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Réservations"
    
    def __str__(self):
        client = self.client_user.get_full_name() if self.client_user else self.client_nom
        return f"{self.logement.titre} - {client} ({self.date_arrivee} à {self.date_depart})"
    
    def save(self, *args, **kwargs):
        """Calculer automatiquement le nombre de nuits et le montant final"""
        # Vérifier que seules les propriétés hotel/residence peuvent être réservées
        if self.logement.account_type not in ['hotel', 'residence']:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                "Les réservations ne sont possibles que pour les propriétés de type 'hotel' ou 'residence'."
            )
        
        self.nombre_nuits = (self.date_depart - self.date_arrivee).days
        self.prix_total = self.prix_par_nuit * self.nombre_nuits
        self.montant_final = self.prix_total + self.frais_service + self.frais_nettoyage_reservation
        super().save(*args, **kwargs)
    
    def clean(self):
        """Valider les réservations"""
        from django.core.exceptions import ValidationError
        
        # Vérifier que seules les propriétés hotel/residence peuvent être réservées
        if self.logement.account_type not in ['hotel', 'residence']:
            raise ValidationError(
                "Les réservations ne sont possibles que pour les propriétés de type 'hotel' ou 'residence'."
            )


class Paiement(models.Model):
    """Modèle pour tracer les paiements (Stripe, Mobile Money, Virement, Cash)"""
    METHODE_CHOICES = [
        ('mouv', '🟠 MOUV (Étoile)'),
        ('orange', '🟠 Orange Money'),
        ('wave', '🔵 Wave'),
        ('stripe', '💳 Carte bancaire (Stripe)'),
        ('virement', '🏦 Virement bancaire'),
        ('cash', '💵 Paiement sur place'),
    ]
    
    STATUT_CHOICES = [
        ('pending', '⏳ En attente'),
        ('completed', '✅ Complété'),
        ('failed', '❌ Échoué'),
        ('refunded', '↩️ Remboursé'),
    ]
    
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='paiement'
    )
    
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    methode = models.CharField(
        max_length=20,
        choices=METHODE_CHOICES,
        default='stripe'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending'
    )
    
    # Référence Stripe
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID de la transaction Stripe"
    )
    stripe_charge_id = models.CharField(
        max_length=255,
        blank=True
    )
    
    # Détails
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Paiements"
    
    def __str__(self):
        return f"{self.reservation.logement.titre} - {self.montant} FCFA ({self.get_statut_display()})"


# ================================
# SIGNAUX POUR LES NOTIFICATIONS
# ================================

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Logement)
def notify_subscribers_on_new_listing(sender, instance, created, **kwargs):
    """Envoyer une notification aux abonnés quand on crée une nouvelle annonce"""
    if created and instance.proprietaire:
        from accounts.models import Subscription, Notification
        
        # Trouver tous les abonnés de ce propriétaire
        subscriptions = Subscription.objects.filter(
            creator=instance.proprietaire,
            is_active=True,
            notify_on_new_listing=True
        ).select_related('subscriber')
        
        # Créer une notification pour chaque abonné
        for subscription in subscriptions:
            Notification.create_new_listing_notification(
                subscriber=subscription.subscriber,
                creator=instance.proprietaire,
                listing=instance
            )
