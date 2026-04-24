from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class ColocationAnnonce(models.Model):
    PROFIL_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('professionnel', 'Professionnel'),
        ('couple', 'Couple'),
        ('famille', 'Famille'),
        ('autre', 'Autre'),
    ]

    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annonces')
    
    # Localisation
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    
    # Budget et logement
    budget_mensuel = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    surface = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    nombre_chambres = models.PositiveSmallIntegerField(default=1)
    nombre_salles_bain = models.PositiveSmallIntegerField(default=1)
    
    # Description
    description = models.TextField()
    infos_logement = models.TextField(blank=True)
    
    # Colocataires
    nombre_colocataires = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    profil_recherche = models.CharField(max_length=20, choices=PROFIL_CHOICES, default='autre', blank=True)
    conditions_vie = models.TextField(blank=True)
    
    # Équipements
    climatisation = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    cuisine_equipee = models.BooleanField(default=False)
    garage = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    
    # Informations supplémentaires
    meuble = models.BooleanField(default=True)
    disponible_depuis = models.DateField(null=True, blank=True)
    durée_minimum = models.PositiveSmallIntegerField(
        default=6, 
        help_text="Durée minimum de location en mois"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ville} – {self.quartier or "Annonce"} ({self.budget_mensuel} FCFA)'

    def clean(self):
        # Only validate if proprietaire is set
        if self.pk and self.proprietaire:
            from accounts.models import Profile
            try:
                profile, created = Profile.objects.get_or_create(user=self.proprietaire)
                if profile.ville and profile.ville.strip().lower() != self.ville.strip().lower():
                    raise ValidationError('Vous ne pouvez publier qu\'une annonce dans votre ville de profil.')
            except Exception:
                pass  # Skip validation if there's an issue accessing profile

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_nombre_photos(self):
        return self.photos.count()


class PhotoColocation(models.Model):
    annonce = models.ForeignKey(
        ColocationAnnonce, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    image = models.ImageField(upload_to='colocations/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Photo de {self.annonce.ville}"


class Favori(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    annonce = models.ForeignKey(ColocationAnnonce, on_delete=models.CASCADE, related_name='favoris')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'annonce')

    def __str__(self):
        return f'{self.utilisateur.username} - {self.annonce}'
