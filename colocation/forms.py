from django import forms
from django.forms import inlineformset_factory
from .models import ColocationAnnonce, PhotoColocation


class ColocationAnnonceForm(forms.ModelForm):
    class Meta:
        model = ColocationAnnonce
        fields = [
            'ville', 'quartier', 'budget_mensuel', 'description',
            'surface', 'nombre_chambres', 'nombre_salles_bain',
            'infos_logement', 'nombre_touristes', 'profil_recherche',
            'conditions_vie', 'meuble', 'disponible_depuis', 'durée_minimum',
            'climatisation', 'wifi', 'cuisine_equipee', 'garage', 'jardin'
        ]
        labels = {
            'ville': 'Ville',
            'quartier': 'Quartier',
            'budget_mensuel': 'Budget mensuel (FCFA)',
            'description': 'Description du logement',
            'surface': 'Surface en m²',
            'nombre_chambres': 'Nombre de chambres',
            'nombre_salles_bain': 'Nombre de salles de bain',
            'infos_logement': 'Informations sur le logement',
            'nombre_touristes': 'Nombre de touristes',
            'profil_recherche': 'Profil recherché',
            'conditions_vie': 'Conditions de vie',
            'meuble': 'Meublé',
            'disponible_depuis': 'Disponible depuis',
            'durée_minimum': 'Durée minimum de location (mois)',
            'climatisation': 'Climatisation',
            'wifi': 'WiFi',
            'cuisine_equipee': 'Cuisine équipée',
            'garage': 'Garage',
            'jardin': 'Jardin',
        }
        widgets = {
            'ville': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Abidjan'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Cocody'
            }),
            'budget_mensuel': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Décrivez votre annonce de colocation...'
            }),
            'surface': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Surface en m²'
            }),
            'nombre_chambres': forms.NumberInput(attrs={'class': 'form-input'}),
            'nombre_salles_bain': forms.NumberInput(attrs={'class': 'form-input'}),
            'infos_logement': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Informations supplémentaires...'
            }),
            'nombre_touristes': forms.NumberInput(attrs={'class': 'form-input'}),
            'profil_recherche': forms.Select(attrs={'class': 'form-select'}),
            'conditions_vie': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Régles de vie, horaires, etc.'
            }),
            'disponible_depuis': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'durée_minimum': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1'
            }),
        }


class PhotoColocationForm(forms.ModelForm):
    class Meta:
        model = PhotoColocation
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
    
    # Rendre l'image optionnelle
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['alt_text'].required = False
        self.fields['order'].required = False
    
    # Valider que si une forme a un changement, elle doit avoir une image
    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        delete = cleaned_data.get('DELETE', False)
        
        # Si le formulaire doit être supprimé, pas besoin d'image
        if delete:
            return cleaned_data
        
        # Si aucune donnée n'a été saisie, c'est acceptable
        if not image and not self.has_changed():
            return cleaned_data
        
        # Si des données ont été saisies mais pas d'image, c'est une erreur
        if self.has_changed() and not image:
            raise forms.ValidationError("Une image est requise si vous saisissez d'autres informations.")
        
        return cleaned_data


PhotoColocationFormSet = inlineformset_factory(
    ColocationAnnonce,
    PhotoColocation,
    form=PhotoColocationForm,
    extra=5,
    max_num=5,
    can_delete=True,
    validate_min=False,  # Ne pas valider le nombre minimum de photos
    validate_max=True,
)


class RechercheAnnonceForm(forms.Form):
    q = forms.CharField(
        label='Mot clé',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Chercher une colocation...'
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
    budget_max = forms.DecimalField(
        label='Budget maximum (FCFA)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Budget max'
        })
    )
    profil_recherche = forms.ChoiceField(
        label='Profil recherché',
        required=False,
        choices=[('', 'Tous les profils')] + list(ColocationAnnonce.PROFIL_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
