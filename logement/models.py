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

    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    
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
    nombre_salles_bain = models.PositiveSmallIntegerField(default=1)
    
    # Équipements
    climatisation = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    garage = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    piscine = models.BooleanField(default=False)
    cuisine_equipee = models.BooleanField(default=False)
    
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


class PhotoLogement(models.Model):
    logement = models.ForeignKey(
        Logement, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    image = models.ImageField(upload_to='logements/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Photo de {self.logement.titre}"
