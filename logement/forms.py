from django import forms
from django.forms import inlineformset_factory
from .models import Logement, PhotoLogement, VideoLogement, Reservation
from datetime import datetime, timedelta

class LogementProprietaireForm(forms.ModelForm):
    """Formulaire pour propriétaire publiant un logement complet"""
    class Meta:
        model = Logement
        fields = [
            # Champs de base
            'titre', 'description', 'type_logement', 'prix',
            'ville', 'quartier',
            
            # Détails
            'surface', 'nombre_pieces', 'nombre_chambres', 'nombre_lits',
            'nombre_salles_bain', 'etage',
            'meuble', 'disponible_depuis',
            
            # Équipements standard
            'climatisation', 'wifi', 'garage', 'jardin', 'piscine', 'cuisine_equipee',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Belle maison moderne à Cocody'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez votre logement en détail...'
            }),
            'type_logement': forms.Select(attrs={'class': 'form-select'}),
            'prix': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Abidjan'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Cocody'
            }),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Surface en m²'
            }),
            'nombre_chambres': forms.NumberInput(attrs={'class': 'form-input'}),
            'nombre_lits': forms.NumberInput(attrs={'class': 'form-input'}),
            'nombre_salles_bain': forms.NumberInput(attrs={'class': 'form-input'}),
            'etage': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optionnel'
            }),
            'disponible_depuis': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class LogementHotelForm(forms.ModelForm):
    """Formulaire spécialisé pour les hôtels"""
    class Meta:
        model = Logement
        fields = [
            # Informations de base
            'titre', 'description', 'ville', 'quartier',
            
            # Caractéristiques de la chambre
            'type_logement', 'surface', 'nombre_lits', 'capacite',
            'nombre_salles_bain', 'etage',
            
            # Tarification hôtel
            'prix_par_nuit', 'frais_nettoyage', 'min_sejour',
            'disponible_depuis',
            
            # Équipements
            'wifi', 'climatisation', 'television', 'minibar', 'coffre_fort',
            'garage', 'reception_24h', 'piscine', 'restaurant',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Chambre Double Climatisée'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez la chambre, les services, la localisation...'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Abidjan'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Plateaux'
            }),
            'type_logement': forms.Select(attrs={'class': 'form-select'}),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0 m²'
            }),
            'nombre_lits': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '1'
            }),
            'capacite': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de personnes'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '1'
            }),
            'etage': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optionnel'
            }),
            'prix_par_nuit': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Prix en FCFA/nuit'
            }),
            'frais_nettoyage': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optionnel (FCFA)'
            }),
            'min_sejour': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '1 nuit minimum'
            }),
            'disponible_depuis': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class LogementResidenceForm(forms.ModelForm):
    """Formulaire spécialisé pour les résidences"""
    class Meta:
        model = Logement
        fields = [
            # Informations de base
            'titre', 'description', 'ville', 'quartier',
            
            # Caractéristiques du logement
            'type_logement', 'surface', 'nombre_pieces', 'nombre_chambres',
            'nombre_salles_bain', 'etage', 'meuble',
            
            # Tarification résidence
            'prix_par_mois', 'caution_mois', 'frais_agence',
            'duree_min_bail', 'type_charge', 'conditions_speciales',
            'disponible_depuis',
            
            # Équipements
            'climatisation', 'wifi', 'garage', 'cuisine_equipee',
            'ascenseur', 'gardien', 'securite', 'buanderie',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Studio Moderne Climatisé'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez le logement, l\'état, l\'ambiance...'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Abidjan'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Cocody'
            }),
            'type_logement': forms.Select(attrs={'class': 'form-select'}),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Surface en m²'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de pièces'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de chambres'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de salles de bain'
            }),
            'etage': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optionnel'
            }),
            'prix_par_mois': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Loyer en FCFA/mois'
            }),
            'caution_mois': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de mois'
            }),
            'frais_agence': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optionnel (FCFA)'
            }),
            'duree_min_bail': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: 1 an, 6 mois...'
            }),
            'type_charge': forms.Select(attrs={'class': 'form-select'}),
            'conditions_speciales': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Ex: Pas d\'animaux, documents requis...'
            }),
            'disponible_depuis': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class LogementColocataireForm(forms.ModelForm):
    """Formulaire pour locataire cherchant un colocataire"""
    class Meta:
        model = Logement
        fields = [
            # Informations de base
            'titre', 'description', 'ville', 'quartier',
            
            # Caractéristiques du logement
            'type_logement', 'surface', 'nombre_pieces', 'nombre_chambres',
            'nombre_lits', 'nombre_salles_bain', 'meuble',
            
            # Tarification colocation
            'prix', 'disponible_depuis',
            
            # Équipements en partage
            'climatisation', 'wifi', 'garage', 'jardin', 'cuisine_equipee',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Cherche colocataire pour beau T3 climatisé'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez votre logement, l\'ambiance, le profil du colocataire recherché...'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Abidjan'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Plateaux'
            }),
            'type_logement': forms.Select(attrs={'class': 'form-select'}),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Surface totale en m²'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de pièces'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de chambres (y compris la vôtre)'
            }),
            'nombre_lits': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre total de lits'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de salles de bain'
            }),
            'prix': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Loyer de la chambre à louer (FCFA/mois)'
            }),
            'disponible_depuis': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class PhotoLogementForm(forms.ModelForm):
    class Meta:
        model = PhotoLogement
        fields = ['image', 'alt_text', 'order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-file-input',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Description de la photo'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
        }
    
    def clean(self):
        """Valider le formulaire - si pas d'image, les autres champs ne sont pas obligatoires"""
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        
        # Si pas d'image, ignorer les erreurs de validation pour alt_text et order
        if not image:
            # Marquer ces champs comme optionnels
            if 'alt_text' in self.errors:
                del self.errors['alt_text']
            if 'order' in self.errors:
                del self.errors['order']
        
        return cleaned_data


PhotoLogementFormSet = inlineformset_factory(
    Logement,
    PhotoLogement,
    form=PhotoLogementForm,
    extra=1,
    max_num=10,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class VideoLogementForm(forms.ModelForm):
    """Formulaire pour ajouter des vidéos"""
    class Meta:
        model = VideoLogement
        fields = ['video', 'titre', 'description', 'order']
        widgets = {
            'video': forms.FileInput(attrs={
                'class': 'form-file-input',
                'accept': 'video/*'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Titre de la vidéo (ex: Visite complète)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Description brève de la vidéo'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
        }
    
    def clean(self):
        """Valider le formulaire - si pas de vidéo, les autres champs ne sont pas obligatoires"""
        cleaned_data = super().clean()
        video = cleaned_data.get('video')
        
        if not video:
            # Si pas de vidéo, ignorer les erreurs pour les autres champs
            if 'titre' in self.errors:
                del self.errors['titre']
            if 'description' in self.errors:
                del self.errors['description']
            if 'order' in self.errors:
                del self.errors['order']
        
        return cleaned_data


VideoLogementFormSet = inlineformset_factory(
    Logement,
    VideoLogement,
    form=VideoLogementForm,
    extra=1,
    max_num=5,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class RechercheLogementForm(forms.Form):
    q = forms.CharField(
        label='Mot clé',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Chercher un logement...'
        })
    )
    ville = forms.CharField(
        label='Ville',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ville'
        })
    )
    prix_max = forms.DecimalField(
        label='Prix maximum',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Prix max'
        })
    )
    type_logement = forms.ChoiceField(
        label='Type de logement',
        required=False,
        choices=[('', 'Tous les types')] + list(Logement.TYPE_LOGEMENT),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReservationForm(forms.ModelForm):
    """Formulaire pour créer une réservation"""
    
    class Meta:
        model = Reservation
        fields = ['date_arrivee', 'date_depart', 'nombre_personnes', 'nombre_chambres', 'client_nom', 'client_email', 'client_telephone', 'remarques']
        widgets = {
            'date_arrivee': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'min': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            }),
            'date_depart': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'min': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            }),
            'nombre_personnes': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'value': '1'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'value': '1'
            }),
            'client_nom': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom complet',
                'required': True
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'votre@email.com',
                'required': True
            }),
            'client_telephone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+225 XX XX XX XX',
                'required': True
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Remarques ou demandes spéciales (optionnel)',
                'rows': 4
            }),
        }
    
    def __init__(self, *args, logement=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logement = logement
        
        # Si utilisateur connecté, préremplir les champs
        if self.initial:
            pass  # Les données viennent de initial
        
        # Rendre nombre_chambres optionnel pour hôtels (une chambre par défaut)
        if logement and logement.account_type == 'hotel':
            self.fields['nombre_chambres'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        date_arrivee = cleaned_data.get('date_arrivee')
        date_depart = cleaned_data.get('date_depart')
        
        # Vérifier que le logement est un hôtel ou une résidence
        if self.logement and self.logement.account_type not in ['hotel', 'residence']:
            raise forms.ValidationError(
                "Les réservations ne sont possibles que pour les hôtels et résidences."
            )
        
        if date_arrivee and date_depart:
            if date_depart <= date_arrivee:
                raise forms.ValidationError(
                    "La date de départ doit être après la date d'arrivée"
                )
            
            # Vérifier les disponibilités
            if self.logement:
                from django.db.models import Q
                from .models import Reservation
                
                conflicting = Reservation.objects.filter(
                    logement=self.logement,
                    statut__in=['confirmed', 'completed'],
                    date_arrivee__lt=date_depart,
                    date_depart__gt=date_arrivee
                ).exists()
                
                if conflicting:
                    raise forms.ValidationError(
                        "Ces dates ne sont pas disponibles pour ce logement"
                    )
        
        return cleaned_data
