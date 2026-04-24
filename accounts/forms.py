from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class SignUpForm(UserCreationForm):
    # Informations personnelles
    first_name = forms.CharField(
        label='Nom',
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Dupont'})
    )
    last_name = forms.CharField(
        label='Prénoms',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Jean Paul'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'exemple@email.com'})
    )
    telephone = forms.CharField(
        label='Numéro de téléphone',
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+225 01 02 03 04 05'})
    )

    # Informations du profil
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label='Type de profil',
    )
    ville = forms.CharField(
        label='Ville',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Abidjan'})
    )
    quartier = forms.CharField(
        label='Quartier',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Plateaux'})
    )
    date_naissance = forms.DateField(
        label='Date de naissance',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    sexe = forms.ChoiceField(
        label='Sexe',
        choices=Profile.SEXE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    profession = forms.CharField(
        label='Profession',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Développeur'})
    )
    photo_profil = forms.ImageField(
        label='Photo de profil',
        required=False,
        help_text='Téléchargez une photo professionnelle (optionnel)'
    )

    # Pièce d'identité
    type_piece_identite = forms.ChoiceField(
        label='Type de pièce d\'identité',
        choices=Profile.PIECE_IDENTITE_CHOICES,
        widget=forms.Select,
        required=True,
        help_text='Sélectionnez votre type de pièce d\'identité'
    )
    numero_piece_identite = forms.CharField(
        label='Numéro de pièce d\'identité',
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: CI123456789'}),
        help_text='Entrez le numéro exact de votre pièce d\'identité'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'telephone',
            'password1',
            'password2',
            'role',
            'ville',
            'quartier',
            'date_naissance',
            'sexe',
            'profession',
            'photo_profil',
            'type_piece_identite',
            'numero_piece_identite',
        ]

    def clean_numero_piece_identite(self):
        numero = self.cleaned_data.get('numero_piece_identite')
        if numero:
            # Vérifier que le numéro n'est pas déjà utilisé
            if Profile.objects.filter(numero_piece_identite=numero).exists():
                raise forms.ValidationError("Ce numéro de pièce d'identité est déjà enregistré.")
        return numero

    def save(self, commit=True):
        user = super().save(commit=commit)
        # Use get_or_create to safely handle profile creation
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = self.cleaned_data['role']
        profile.ville = self.cleaned_data['ville']
        profile.quartier = self.cleaned_data.get('quartier', '')
        profile.date_naissance = self.cleaned_data['date_naissance']
        profile.sexe = self.cleaned_data['sexe']
        profile.profession = self.cleaned_data['profession']
        profile.telephone = self.cleaned_data['telephone']
        profile.photo_profil = self.cleaned_data['photo_profil']
        profile.type_piece_identite = self.cleaned_data['type_piece_identite']
        profile.numero_piece_identite = self.cleaned_data['numero_piece_identite']
        if commit:
            profile.save()
        return user
        return user


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nom',
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Dupont'})
    )
    last_name = forms.CharField(
        label='Prénoms',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Jean Paul'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'exemple@email.com'})
    )

    class Meta:
        model = Profile
        fields = [
            'telephone',
            'ville',
            'quartier',
            'profession',
            'photo_profil',
            'type_piece_identite',
            'numero_piece_identite'
        ]
        widgets = {
            'telephone': forms.TextInput(attrs={'placeholder': '+225 01 02 03 04 05'}),
            'ville': forms.TextInput(attrs={'placeholder': 'Ex: Abidjan'}),
            'quartier': forms.TextInput(attrs={'placeholder': 'Ex: Plateaux'}),
            'profession': forms.TextInput(attrs={'placeholder': 'Ex: Développeur'}),
            'numero_piece_identite': forms.TextInput(attrs={'placeholder': 'Ex: CI123456789'}),
        }
        labels = {
            'telephone': 'Téléphone',
            'ville': 'Ville',
            'quartier': 'Quartier',
            'profession': 'Profession',
            'photo_profil': 'Photo de profil',
            'type_piece_identite': 'Type de pièce d\'identité',
            'numero_piece_identite': 'Numéro de pièce d\'identité',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
