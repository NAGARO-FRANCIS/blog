from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import BlocageCalendrier, Logement, PhotoLogement, VideoLogement, Reservation
from datetime import datetime, timedelta


LOGEMENT_FIELD_LABELS = {
    'titre': _('Titre'),
    'description': _('Description'),
    'type_logement': _('Type de logement'),
    'prix': _('Prix'),
    'ville': _('Ville'),
    'quartier': _('Quartier'),
    'surface': _('Surface'),
    'nombre_pieces': _('Nombre de pièces'),
    'nombre_chambres': _('Nombre de chambres'),
    'nombre_lits': _('Nombre de lits'),
    'nombre_salles_bain': _('Nombre de salles de bain'),
    'etage': _('Étage'),
    'meuble': _('Meublé'),
    'disponible_depuis': _('Disponible à partir du'),
    'latitude': _('Latitude'),
    'longitude': _('Longitude'),
    'distance_universite': _('Distance à l’université (km)'),
    'distance_hopital': _('Distance à l’hôpital (km)'),
    'capacite': _('Capacité'),
    'unites_totales': _('Nombre total d’unités'),
    'prix_par_nuit': _('Prix par nuit'),
    'prix_par_mois': _('Prix par mois'),
    'frais_nettoyage': _('Frais de nettoyage'),
    'min_sejour': _('Séjour minimum'),
    'politique_annulation': _('Politique d’annulation'),
    'heure_arrivee': _('Heure d’arrivée'),
    'heure_depart': _('Heure de départ'),
    'caution_mois': _('Mois de caution'),
    'frais_agence': _('Frais d’agence'),
    'duree_min_bail': _('Durée minimale du bail'),
    'type_charge': _('Type de charges'),
    'conditions_speciales': _('Conditions spéciales'),
    'climatisation': _('Climatisation'),
    'wifi': _('Wi-Fi'),
    'garage': _('Garage'),
    'jardin': _('Jardin'),
    'piscine': _('Piscine'),
    'cuisine_equipee': _('Cuisine équipée'),
    'minibar': _('Minibar'),
    'television': _('Télévision'),
    'coffre_fort': _('Coffre-fort'),
    'reception_24h': _('Réception 24h'),
    'restaurant': _('Restaurant'),
    'ascenseur': _('Ascenseur'),
    'gardien': _('Gardien'),
    'securite': _('Sécurité'),
    'buanderie': _('Buanderie'),
    'image': _('Photo'),
    'alt_text': _('Description de la photo'),
    'order': _('Ordre d’affichage'),
    'video': _('Vidéo'),
    'date_arrivee': _('Date d’arrivée'),
    'date_depart': _('Date de départ'),
    'nombre_personnes': _('Nombre de personnes'),
    'client_nom': _('Nom complet'),
    'client_email': _('Adresse e-mail'),
    'client_telephone': _('Téléphone'),
    'remarques': _('Remarques'),
    'logement': _('Logement'),
    'date_debut': _('Date de début'),
    'date_fin': _('Date de fin'),
    'motif': _('Motif'),
}


class LocalizedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, label in LOGEMENT_FIELD_LABELS.items():
            if field_name in self.fields:
                self.fields[field_name].label = label


class LogementProprietaireForm(LocalizedModelForm):
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs optionnels avec valeurs par défaut
        self.fields['surface'].required = False
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_chambres'].required = False
        self.fields['nombre_lits'].required = False
        self.fields['nombre_salles_bain'].required = False
        self.fields['etage'].required = False
        self.fields['prix'].required = False
    
    def clean(self):
        """Valider et remplir les champs optionnels avec des valeurs par défaut"""
        cleaned_data = super().clean()
        
        # Remplir avec des valeurs par défaut si vides
        if not cleaned_data.get('surface'):
            cleaned_data['surface'] = 50
        if not cleaned_data.get('nombre_pieces'):
            cleaned_data['nombre_pieces'] = 2
        if not cleaned_data.get('nombre_chambres'):
            cleaned_data['nombre_chambres'] = 1
        if not cleaned_data.get('nombre_salles_bain'):
            cleaned_data['nombre_salles_bain'] = 1
        if not cleaned_data.get('prix'):
            cleaned_data['prix'] = 0
        
        return cleaned_data


class LogementHotelForm(LocalizedModelForm):
    """Formulaire spécialisé pour les hôtels"""
    class Meta:
        model = Logement
        fields = [
            # Informations de base
            'titre', 'description', 'ville', 'quartier',
            'latitude', 'longitude', 'distance_universite', 'distance_hopital',
            
            # Caractéristiques de la chambre
            'type_logement', 'surface', 'nombre_pieces', 'nombre_lits', 'capacite', 'unites_totales',
            'nombre_salles_bain', 'etage',
            
            # Tarification hôtel
            'prix_par_nuit', 'frais_nettoyage', 'min_sejour', 'politique_annulation', 'heure_arrivee', 'heure_depart',
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
            'latitude': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: 5.3364',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: -4.0267',
                'step': 'any'
            }),
            'distance_universite': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: 2.5',
                'step': '0.01',
                'min': '0'
            }),
            'distance_hopital': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: 1.8',
                'step': '0.01',
                'min': '0'
            }),
            'type_logement': forms.Select(attrs={'class': 'form-select'}),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0 m²'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre d espaces'
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_logement'].choices = [
            ('', _('Sélectionnez le type de chambre')),
            ('simple', _('Chambre simple')),
            ('double', _('Chambre double')),
            ('duplex', _('Duplex')),
            ('suite', _('Suite')),
            ('familiale', _('Chambre familiale')),
        ]
        # Rendre les champs optionnels avec valeurs par défaut
        self.fields['surface'].required = False
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_lits'].required = False
        self.fields['capacite'].required = False
        self.fields['nombre_salles_bain'].required = False
        self.fields['etage'].required = False
        self.fields['prix_par_nuit'].required = True
        self.fields['prix_par_nuit'].min_value = 0.01
        self.fields['prix_par_nuit'].widget.attrs.update({'min': '0.01', 'step': '0.01', 'required': True})
        self.fields['frais_nettoyage'].required = False
        self.fields['min_sejour'].required = False
    
    def clean(self):
        """Valider et remplir les champs optionnels avec des valeurs par défaut"""
        cleaned_data = super().clean()
        
        # Remplir avec des valeurs par défaut si vides
        if not cleaned_data.get('surface'):
            cleaned_data['surface'] = 20  # Valeur par défaut pour chambre d'hôtel
        if not cleaned_data.get('nombre_lits'):
            cleaned_data['nombre_lits'] = 1
        if not cleaned_data.get('capacite'):
            cleaned_data['capacite'] = 2
        if not cleaned_data.get('nombre_salles_bain'):
            cleaned_data['nombre_salles_bain'] = 1
        if not cleaned_data.get('min_sejour'):
            cleaned_data['min_sejour'] = 1
        
        return cleaned_data


class LogementResidenceForm(LocalizedModelForm):
    """Formulaire spécialisé pour les résidences"""
    class Meta:
        model = Logement
        fields = [
            # Informations de base
            'titre', 'description', 'ville', 'quartier',
            
            # Caractéristiques du logement
            'type_logement', 'surface', 'nombre_pieces', 'nombre_chambres', 'unites_totales',
            'nombre_salles_bain', 'etage', 'meuble',
            
            # Tarification résidence
            'prix_par_nuit', 'prix_par_mois', 'caution_mois', 'frais_agence',
            'duree_min_bail', 'type_charge', 'conditions_speciales', 'politique_annulation', 'heure_arrivee', 'heure_depart',
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
            'prix_par_nuit': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Prix journalier en FCFA',
                'min': '0.01',
                'step': '0.01',
                'required': True,
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs de détails optionnels avec valeurs par défaut
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_chambres'].required = False
        self.fields['nombre_salles_bain'].required = False
        self.fields['etage'].required = False
        self.fields['surface'].required = False
        self.fields['prix_par_mois'].required = False
        self.fields['prix_par_nuit'].required = True
        self.fields['prix_par_nuit'].min_value = 0.01
        self.fields['prix_par_nuit'].widget.attrs.update({'min': '0.01', 'step': '0.01', 'required': True})
        self.fields['caution_mois'].required = False
    
    def clean(self):
        """Valider et remplir les champs optionnels avec des valeurs par défaut"""
        cleaned_data = super().clean()
        
        # Remplir avec des valeurs par défaut si vides
        if not cleaned_data.get('nombre_pieces'):
            cleaned_data['nombre_pieces'] = 1
        if not cleaned_data.get('nombre_chambres'):
            cleaned_data['nombre_chambres'] = 1
        if not cleaned_data.get('nombre_salles_bain'):
            cleaned_data['nombre_salles_bain'] = 1
        if not cleaned_data.get('surface'):
            cleaned_data['surface'] = 30  # Valeur par défaut
        if not cleaned_data.get('caution_mois'):
            cleaned_data['caution_mois'] = 2
        
        return cleaned_data


class LogementTouristeForm(LocalizedModelForm):
    """Formulaire pour locataire cherchant un touriste"""
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
                'placeholder': 'Ex: Cherche touriste pour beau T3 climatisé'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez votre logement, l\'ambiance, le profil du touriste recherché...'
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs optionnels avec valeurs par défaut
        self.fields['surface'].required = False
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_chambres'].required = False
        self.fields['nombre_lits'].required = False
        self.fields['nombre_salles_bain'].required = False
        self.fields['prix'].required = False
    
    def clean(self):
        """Valider et remplir les champs optionnels avec des valeurs par défaut"""
        cleaned_data = super().clean()
        
        # Remplir avec des valeurs par défaut si vides
        if not cleaned_data.get('surface'):
            cleaned_data['surface'] = 60
        if not cleaned_data.get('nombre_pieces'):
            cleaned_data['nombre_pieces'] = 2
        if not cleaned_data.get('nombre_chambres'):
            cleaned_data['nombre_chambres'] = 2
        if not cleaned_data.get('nombre_lits'):
            cleaned_data['nombre_lits'] = 2
        if not cleaned_data.get('nombre_salles_bain'):
            cleaned_data['nombre_salles_bain'] = 1
        if not cleaned_data.get('prix'):
            cleaned_data['prix'] = 0
        
        return cleaned_data


class PhotoLogementForm(LocalizedModelForm):
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
        
        # Assigner une valeur par défaut à order s'il est vide
        if not cleaned_data.get('order'):
            cleaned_data['order'] = 0
        
        return cleaned_data


PhotoLogementFormSet = inlineformset_factory(
    Logement,
    PhotoLogement,
    form=PhotoLogementForm,
    extra=3,
    max_num=20,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class VideoLogementForm(LocalizedModelForm):
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
        
        # Assigner une valeur par défaut à order s'il est vide
        if not cleaned_data.get('order'):
            cleaned_data['order'] = 0
        
        return cleaned_data


VideoLogementFormSet = inlineformset_factory(
    Logement,
    VideoLogement,
    form=VideoLogementForm,
    extra=3,
    max_num=10,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class RechercheLogementForm(forms.Form):
    q = forms.CharField(
        label=_('Mot clé'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Chercher un logement...')
        })
    )
    ville = forms.CharField(
        label=_('Ville'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Ville')
        })
    )
    commune = forms.CharField(label=_('Commune'), required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Commune')}))
    quartier = forms.CharField(label=_('Quartier'), required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Quartier')}))
    prix_min = forms.DecimalField(label=_('Prix minimum'), required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': _('Prix min')}))
    prix_max = forms.DecimalField(
        label=_('Prix maximum'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': _('Prix max')
        })
    )
    nombre_chambres_min = forms.IntegerField(label=_('Chambres minimum'), required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}))
    type_logement = forms.ChoiceField(
        label=_('Type de logement'),
        required=False,
        choices=[('', _('Tous les types'))] + list(Logement.TYPE_LOGEMENT),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    account_type = forms.ChoiceField(
        required=False,
        choices=[('', _('Tous les comptes'))] + list(Logement.ACCOUNT_TYPE),
        widget=forms.HiddenInput()
    )
    _availability_choices = [('', _('Indifférent')), ('1', _('Oui')), ('0', _('Non'))]
    meuble = forms.ChoiceField(label=_('Meublé'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    wifi = forms.ChoiceField(label='WiFi', required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    garage = forms.ChoiceField(label=_('Garage'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    climatisation = forms.ChoiceField(label=_('Climatisation'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    securite = forms.ChoiceField(label=_('Sécurité'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    eau = forms.ChoiceField(label=_('Eau'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    electricite = forms.ChoiceField(label=_('Électricité'), required=False, choices=_availability_choices, widget=forms.Select(attrs={'class': 'form-select'}))
    distance_universite_max = forms.DecimalField(label=_('Distance université maximale'), required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'step': '0.01'}))
    distance_hopital_max = forms.DecimalField(label=_('Distance hôpital maximale'), required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'step': '0.01'}))
    disponible_immediatement = forms.BooleanField(label=_('Disponible immédiatement'), required=False)


class CategoryLogementChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, logement):
        return _('%(category)s — %(title)s — %(price)s FCFA / jour') % {
            'category': logement.get_type_logement_display(),
            'title': logement.titre,
            'price': logement.prix_journalier,
        }


class ReservationForm(LocalizedModelForm):
    """Formulaire pour créer une réservation"""
    
    class Meta:
        model = Reservation
        fields = ['date_arrivee', 'date_depart', 'nombre_personnes', 'nombre_chambres', 'client_nom', 'client_email', 'client_telephone', 'remarques']
        labels = {
            'date_arrivee': _('Date d’arrivée'),
            'date_depart': _('Date de départ'),
            'nombre_personnes': _('Nombre de personnes'),
            'nombre_chambres': _('Nombre de chambres'),
            'client_nom': _('Nom complet'),
            'client_email': _('Adresse e-mail'),
            'client_telephone': _('Téléphone'),
            'remarques': _('Remarques'),
        }
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
                'placeholder': _('Votre nom complet'),
                'required': True
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('votre@email.com'),
                'required': True
            }),
            'client_telephone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+225 XX XX XX XX',
                'required': True
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': _('Remarques ou demandes spéciales (optionnel)'),
                'rows': 4
            }),
        }
    
    def __init__(self, *args, logement=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logement = logement
        self.category_prices = {}

        if logement and logement.etablissement_id:
            categories = Logement.objects.filter(
                etablissement_id=logement.etablissement_id,
                account_type=logement.account_type,
            ).order_by('type_logement', 'titre')
            if categories.count() > 1:
                available_categories = categories.filter(
                    Q(prix_par_nuit__gt=0)
                    | (Q(account_type='hotel') & Q(prix__gt=0))
                )
                self.fields['categorie_logement'] = CategoryLogementChoiceField(
                    label=_('Catégorie du logement'),
                    queryset=available_categories,
                    empty_label=_('Choisissez une catégorie'),
                    required=True,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                )
                if available_categories.filter(pk=logement.pk).exists():
                    self.initial['categorie_logement'] = logement.pk
                self.category_prices = {
                    str(category.pk): {
                        'title': category.titre,
                        'price': str(category.prix_journalier),
                    }
                    for category in available_categories
                }
        
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
        logement_reserve = cleaned_data.get('categorie_logement') or self.logement
        
        # Vérifier que le logement est un hôtel ou une résidence
        if logement_reserve and logement_reserve.account_type not in ['hotel', 'residence']:
            raise forms.ValidationError(
                _("Les réservations ne sont possibles que pour les hôtels et résidences.")
            )

        if logement_reserve and (
            logement_reserve.prix_journalier is None
            or logement_reserve.prix_journalier <= 0
        ):
            self.add_error(
                'categorie_logement' if 'categorie_logement' in self.fields else None,
                _("Cette catégorie n'a pas de tarif journalier renseigné."),
            )
            return cleaned_data

        if date_arrivee and date_depart:
            if date_depart <= date_arrivee:
                raise forms.ValidationError(
                    _("La date de départ doit être après la date d'arrivée")
                )
            
            if logement_reserve:
                requested_units = cleaned_data.get('nombre_chambres') or 1
                if logement_reserve.available_units_for_period(
                    date_arrivee,
                    date_depart,
                ).count() < requested_units:
                    raise forms.ValidationError(
                        _("Il ne reste pas assez de chambres disponibles pour toute la durée du séjour.")
                    )
        
        return cleaned_data


class BlocageCalendrierForm(LocalizedModelForm):
    class Meta:
        model = BlocageCalendrier
        fields = ['logement', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'motif': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Travaux, fermeture annuelle...'}),
            'logement': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('date_debut') and cleaned_data.get('date_fin') and cleaned_data['date_fin'] <= cleaned_data['date_debut']:
            raise forms.ValidationError('La date de fin doit être après la date de début.')
        return cleaned_data
