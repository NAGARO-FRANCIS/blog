from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
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
    verified = models.BooleanField(default=False)
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
        return self.verified

    @property
    def ville_residence(self):
        return self.ville

    def clean(self):
        from django.core.exceptions import ValidationError
        # Allow telephone to be empty for new profiles
        pass


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
