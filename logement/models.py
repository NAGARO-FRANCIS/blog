from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Etablissement(models.Model):
    """Etablissement professionnel regroupant ses categories de logements."""

    TYPE_CHOICES = [
        ('hotel', _('Hotel')),
        ('residence', _('Residence')),
    ]

    proprietaire = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='etablissement_logement',
    )
    nom = models.CharField(max_length=200)
    type_etablissement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    ville = models.CharField(max_length=100)
    commune = models.CharField(max_length=100, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    eau = models.BooleanField(default=False)
    electricite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Etablissement'
        verbose_name_plural = 'Etablissements'

    def __str__(self):
        return self.nom


class Logement(models.Model):
    TYPE_LOGEMENT = [
        ('appartement', _('Appartement')),
        ('maison', _('Maison')),
        ('studio', _('Studio')),
        ('villa', _('Villa')),
        ('chambre', _('Chambre')),
        ('simple', _('Chambre simple')),
        ('double', _('Chambre double')),
        ('duplex', _('Duplex')),
        ('suite', _('Suite')),
        ('familiale', _('Chambre familiale')),
    ]
    
    ACCOUNT_TYPE = [
        ('hotel', _('Hôtel')),
        ('residence', _('Résidence')),
        ('individu', _('Individu')),
    ]
    
    TYPE_CHARGE = [
        ('charges_comprises', _('Charges comprises')),
        ('charges_non_comprises', _('Charges non comprises')),
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
    unites_totales = models.PositiveIntegerField(
        default=1,
        help_text='Nombre de chambres/appartements de cette catégorie',
    )
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
    politique_annulation = models.TextField(blank=True)
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    
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
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_universite = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Distance en km')
    distance_hopital = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Distance en km')
    
    proprietaire = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logements',
    )
    etablissement = models.ForeignKey(
        Etablissement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories',
        help_text='Etablissement auquel cette chambre ou ce logement appartient',
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

    def reserved_units_for_date(self, day):
        reservations = self.reservations.filter(
            date_arrivee__lte=day,
            date_depart__gt=day,
            statut__in=['pending', 'confirmed'],
        ).prefetch_related('unites')
        return sum(
            len(reservation.unites.all()) or reservation.nombre_chambres or 1
            for reservation in reservations
        )

    def available_units_for_date(self, day):
        if self.disponibilites.filter(date=day, statut='bloquer').exists():
            return 0
        if self.blocages.filter(date_debut__lte=day, date_fin__gt=day).exists():
            return 0
        return max(self.unites_totales - self.reserved_units_for_date(day), 0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.account_type in ['hotel', 'residence']:
            existing_numbers = set(self.unites.values_list('numero', flat=True))
            missing_units = [
                UniteLogement(logement=self, numero=str(number))
                for number in range(1, self.unites_totales + 1)
                if str(number) not in existing_numbers
            ]
            UniteLogement.objects.bulk_create(missing_units, ignore_conflicts=True)

    def available_units_for_period(self, start_date, end_date):
        if self.blocages.filter(
            date_debut__lt=end_date,
            date_fin__gt=start_date,
        ).exists() or self.disponibilites.filter(
            date__gte=start_date,
            date__lt=end_date,
            statut__in=['bloquer', 'occupe'],
        ).exists():
            return UniteLogement.objects.none()

        overlapping_reservations = Reservation.objects.filter(
            logement=self,
            statut__in=['pending', 'confirmed'],
            date_arrivee__lt=end_date,
            date_depart__gt=start_date,
        ).prefetch_related('unites')
        reserved_unit_ids = set()
        unassigned_units = 0
        for reservation in overlapping_reservations:
            assigned_units = list(reservation.unites.all())
            reserved_unit_ids.update(unit.pk for unit in assigned_units)
            unassigned_units += max(
                (reservation.nombre_chambres or 1) - len(assigned_units),
                0,
            )

        available_units = self.unites.exclude(id__in=reserved_unit_ids).order_by('id')
        return available_units[unassigned_units:]

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
        ('disponible', _('✅ Disponible')),
        ('occupe', _('❌ Occupé')),
        ('bloquer', _('🚫 Bloqué')),
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


class BlocageCalendrier(models.Model):
    """Période bloquée par le professionnel, par exemple pour travaux."""
    logement = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='blocages')
    date_debut = models.DateField()
    date_fin = models.DateField(help_text='Date de fin exclusive')
    motif = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_debut']

    def __str__(self):
        return f'{self.logement} - {self.date_debut} au {self.date_fin}'


class UniteLogement(models.Model):
    """Unité numérotée pouvant être attribuée à une réservation."""
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name='unites',
    )
    numero = models.CharField(max_length=30)

    class Meta:
        ordering = ['numero']
        constraints = [
            models.UniqueConstraint(
                fields=['logement', 'numero'],
                name='unique_numero_unite_par_logement',
            ),
        ]

    def __str__(self):
        return f'{self.logement.titre} — chambre {self.numero}'


class Reservation(models.Model):
    """Modèle pour les réservations (hôtels, résidences, touristes)"""
    STATUT_CHOICES = [
        ('pending', _('⏳ En attente de paiement')),
        ('confirmed', _('✅ Confirmée')),
        ('cancelled', _('❌ Annulée')),
        ('completed', _('✓ Complétée')),
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
    unites = models.ManyToManyField(
        UniteLogement,
        blank=True,
        related_name='reservations',
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
        if self.logement_id:  # Vérifier que le logement est assigné
            try:
                if self.logement.account_type not in ['hotel', 'residence']:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        "Les réservations ne sont possibles que pour les propriétés de type 'hotel' ou 'residence'."
                    )
            except Exception:
                pass  # Si erreur d'accès, laisser passer (sera validé après)
        
        self.nombre_nuits = (self.date_depart - self.date_arrivee).days
        self.prix_total = self.prix_par_nuit * self.nombre_nuits
        self.montant_final = self.prix_total + self.frais_service + self.frais_nettoyage_reservation
        super().save(*args, **kwargs)
    
    def clean(self):
        """Valider les réservations"""
        from django.core.exceptions import ValidationError
        
        # Vérifier que seules les propriétés hotel/residence peuvent être réservées
        if self.logement_id:  # Vérifier que le logement est assigné
            try:
                if self.logement.account_type not in ['hotel', 'residence']:
                    raise ValidationError(
                        "Les réservations ne sont possibles que pour les propriétés de type 'hotel' ou 'residence'."
                    )
            except Exception:
                pass  # Si erreur d'accès, laisser passer


class AvisLogement(models.Model):
    """Avis vérifié, rattaché à une réservation réellement effectuée."""
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name='avis',
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='avis',
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avis_logements',
    )
    note_logement = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    note_proprietaire = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    commentaire = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reponses',
    )
    est_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reservation', 'auteur'],
                name='unique_avis_par_reservation',
            ),
        ]
        verbose_name = 'Avis logement'
        verbose_name_plural = 'Avis logements'

    def __str__(self):
        return f'Avis de {self.auteur} sur {self.logement}'

    @property
    def est_reponse(self):
        return self.parent_id is not None


class SignalementAvis(models.Model):
    """Signalement d'un avis par un utilisateur, traité par la modération."""
    avis = models.ForeignKey(
        AvisLogement,
        on_delete=models.CASCADE,
        related_name='signalements',
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='signalements_avis',
    )
    motif = models.CharField(max_length=500)
    traite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['avis', 'auteur'],
                name='unique_signalement_avis_par_utilisateur',
            ),
        ]

    def __str__(self):
        return f'Signalement de l\'avis {self.avis_id}'


class Paiement(models.Model):
    """Modèle pour tracer les paiements (Stripe, Mobile Money, Virement, Cash)"""
    METHODE_CHOICES = [
        ('mobile_money', _('📱 Mobile Money (Orange, MOUV, Moov, Wave)')),
        ('mouv', _('🟠 MOUV (ancien)')),
        ('orange', _('🟠 Orange Money (ancien)')),
        ('wave', _('🔵 Wave (ancien)')),
        ('stripe', _('💳 Carte bancaire (Stripe)')),
        ('virement', _('🏦 Virement bancaire')),
        ('cash', _('💵 Paiement sur place')),
    ]
    
    STATUT_CHOICES = [
        ('pending', _('⏳ En attente')),
        ('completed', _('✅ Complété')),
        ('failed', _('❌ Échoué')),
        ('refunded', _('↩️ Remboursé')),
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

    # Références CinetPay
    cinetpay_payment_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="payment_token renvoyé par CinetPay à l'initialisation"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text='Identifiant unique envoyé à CinetPay pour cette transaction'
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
# MODÈLE FAVORIS
# ================================

class FavoriLogement(models.Model):
    """Modèle pour gérer les favoris des utilisateurs"""
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris_logements')
    logement = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='favoris_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'logement')
        ordering = ['-created_at']
        verbose_name_plural = "Favoris Logements"

    def __str__(self):
        return f'{self.utilisateur.username} - {self.logement.titre}'


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


@receiver(post_save, sender=Paiement)
def notify_on_completed_payment(sender, instance, created, **kwargs):
    """Notifier une seule fois le paiement réellement marqué comme reçu."""
    if instance.statut != 'completed':
        return
    from accounts.models import Notification
    if Notification.objects.filter(related_payment_id=instance.id, notification_type='payment').exists():
        return
    from accounts.notification_service import payment_received
    payment_received(instance)
