from django import forms
from django.forms import inlineformset_factory
from .models import Logement, PhotoLogement

class LogementForm(forms.ModelForm):
    class Meta:
        model = Logement
        fields = [
            'titre', 'description', 'type_logement', 'prix', 
            'ville', 'quartier', 'surface', 'nombre_pieces',
            'nombre_chambres', 'nombre_salles_bain', 'etage',
            'meuble', 'disponible_depuis',
            'climatisation', 'wifi', 'garage', 'jardin', 'piscine', 'cuisine_equipee'
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
            'nombre_pieces': forms.NumberInput(attrs={'class': 'form-input'}),
            'nombre_chambres': forms.NumberInput(attrs={'class': 'form-input'}),
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


PhotoLogementFormSet = inlineformset_factory(
    Logement,
    PhotoLogement,
    form=PhotoLogementForm,
    extra=5,
    max_num=5,
    can_delete=True
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
