from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, ProfessionalProfile
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def process_image(uploaded, size=(512, 512)):
    if not uploaded:
        return None
    try:
        image = Image.open(uploaded)
        image = image.convert('RGB')
        image.thumbnail(size, Image.LANCZOS)
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG', quality=85)
        thumb_io.seek(0)
        return SimpleUploadedFile(uploaded.name, thumb_io.read(), content_type='image/jpeg')
    except Exception:
        return uploaded


class AccountTypeForm(forms.Form):
    """Formulaire de choix du type de compte lors de l'inscription"""
    ACCOUNT_TYPE_CHOICES = [
        ('individu', 'Je suis un individu (cherche colocation/logement)'),
        ('residence', 'Je gère une résidence'),
        ('hotel', 'Je gère un hôtel'),
    ]
    
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label='Quel est votre type de compte ?',
        help_text='Sélectionnez l\'option qui correspond à votre profil'
    )


class IndividuRoleForm(forms.Form):
    """Formulaire de choix du rôle pour les individus"""
    ROLE_CHOICES = [
        ('proprietaire', '🏠 Propriétaire - Je possède une maison et veux louer les chambres'),
        ('locataire', '🔑 Locataire - J\'ai une maison et cherche un touriste'),
        ('touriste', '👥 Touriste - Je cherche une chambre/maison à louer'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label='Quel est votre rôle ?',
        help_text='Sélectionnez le rôle qui correspond à votre situation'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des descriptions pour chaque rôle
        self.fields['role'].help_text = """
        <div style="margin-top: 1rem;">
            <p><strong>📝 Propriétaire :</strong> Vous possédez une maison et souhaitez louer les chambres à des locataires</p>
            <p><strong>📝 Locataire :</strong> Vous avez déjà une maison et cherchez quelqu'un pour partager les frais</p>
            <p><strong>📝 Touriste :</strong> Vous cherchez une chambre ou maison à louer (vous ne pouvez pas publier d'annonces)</p>
        </div>
        """


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
        help_text='Téléchargez une photo professionnelle (optionnel)',
        widget=forms.FileInput(attrs={
            'accept': 'image/jpeg,image/png,image/gif',
            'class': 'file-input',
            'id': 'photoInput'
        })
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Cet email est déjà utilisé.')
        return email

    def _process_image(self, uploaded, size=(512, 512)):
        if not uploaded:
            return None
        try:
            image = Image.open(uploaded)
            image = image.convert('RGB')
            image.thumbnail(size, Image.LANCZOS)
            thumb_io = BytesIO()
            image.save(thumb_io, format='JPEG', quality=85)
            thumb_io.seek(0)
            return SimpleUploadedFile(uploaded.name, thumb_io.read(), content_type='image/jpeg')
        except Exception:
            return uploaded

    def save(self, commit=True):
        user = super().save(commit=commit)
        # Use get_or_create to safely handle profile creation
        profile, created = Profile.objects.get_or_create(user=user)
        # Only set role if it's in cleaned_data (it comes from session in the view)
        if 'role' in self.cleaned_data:
            profile.role = self.cleaned_data['role']
        # Only set account_type if it's in cleaned_data (it comes from session in the view)
        if 'account_type' in self.cleaned_data:
            profile.account_type = self.cleaned_data.get('account_type', 'individu')
        profile.ville = self.cleaned_data['ville']
        profile.quartier = self.cleaned_data.get('quartier', '')
        profile.date_naissance = self.cleaned_data['date_naissance']
        profile.sexe = self.cleaned_data['sexe']
        profile.profession = self.cleaned_data['profession']
        profile.telephone = self.cleaned_data['telephone']
        photo = self.cleaned_data.get('photo_profil')
        if photo:
            profile.photo_profil = self._process_image(photo)
        profile.type_piece_identite = self.cleaned_data['type_piece_identite']
        profile.numero_piece_identite = self.cleaned_data['numero_piece_identite']
        if commit:
            profile.save()
        return user


class ProfessionalSignUpForm(UserCreationForm):
    """Formulaire d'inscription pour les professionnels (Résidence/Hôtel)"""
    # Informations personnelles du représentant
    first_name = forms.CharField(
        label='Nom du représentant légal',
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Dupont'})
    )
    last_name = forms.CharField(
        label='Prénoms du représentant',
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
        label='Numéro de téléphone personnel',
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+225 01 02 03 04 05'})
    )
    
    # Informations de l'établissement
    establishment_name = forms.CharField(
        label='Nom officiel de l\'établissement',
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Résidence La Paix'})
    )
    siret_or_rccm = forms.CharField(
        label='SIRET ou RCCM',
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Numéro SIRET/RCCM'}),
        help_text='SIRET pour la France, RCCM pour la Côte d\'Ivoire'
    )
    legal_phone = forms.CharField(
        label='Téléphone de l\'établissement',
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+225 01 02 03 04 05'})
    )
    
    # Adresse de l'établissement
    establishment_address = forms.CharField(
        label='Adresse complète',
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Rue de la Paix, Plateaux'})
    )
    establishment_city = forms.CharField(
        label='Ville',
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Abidjan'})
    )
    establishment_postal_code = forms.CharField(
        label='Code postal',
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={'placeholder': '00000'})
    )
    
    # Détails de l'établissement
    number_of_rooms = forms.IntegerField(
        label='Nombre de chambres/unités',
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '10'})
    )
    number_of_floors = forms.IntegerField(
        label='Nombre d\'étages',
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '3'})
    )
    website = forms.URLField(
        label='Site web',
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://example.com'})
    )
    
    # Documents
    legal_document = forms.FileField(
        label='Document légal de constitution',
        required=True,
        help_text='PDF ou image',
        widget=forms.FileInput(attrs={'accept': '.pdf,image/*'})
    )
    establishment_photo = forms.ImageField(
        label='Photo de façade de l\'établissement',
        required=True,
        help_text='Photo claire de la façade',
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    
    # Pièce d'identité du représentant
    type_piece_identite = forms.ChoiceField(
        label='Type de pièce d\'identité',
        choices=Profile.PIECE_IDENTITE_CHOICES,
        widget=forms.Select,
        required=True
    )
    numero_piece_identite = forms.CharField(
        label='Numéro de pièce d\'identité',
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: CI123456789'})
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
        ]

    def clean_siret_or_rccm(self):
        siret = self.cleaned_data.get('siret_or_rccm')
        if siret and ProfessionalProfile.objects.filter(siret_or_rccm=siret).exists():
            raise forms.ValidationError("Ce numéro SIRET/RCCM est déjà enregistré.")
        return siret

    def clean_numero_piece_identite(self):
        numero = self.cleaned_data.get('numero_piece_identite')
        if numero and Profile.objects.filter(numero_piece_identite=numero).exists():
            raise forms.ValidationError("Ce numéro de pièce d'identité est déjà enregistré.")
        return numero

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Cet email est déjà utilisé.')
        return email

    def save(self, commit=True, establishment_type='residence'):
        user = super().save(commit=commit)
        
        # Assurer que establishment_type est valide
        if establishment_type not in ['residence', 'hotel']:
            establishment_type = 'residence'
        
        # Créer le profil avec le bon account_type
        profile, created = Profile.objects.get_or_create(user=user)
        profile.account_type = establishment_type
        profile.role = 'proprietaire'
        profile.profession = f"Gestionnaire de {establishment_type}"
        profile.ville = self.cleaned_data['establishment_city']
        profile.profession = f"Gestionnaire de {establishment_type}"
        profile.telephone = self.cleaned_data['telephone']
        profile.type_piece_identite = self.cleaned_data['type_piece_identite']
        profile.numero_piece_identite = self.cleaned_data['numero_piece_identite']
        if commit:
            profile.save()
        
        # Créer le profil professionnel avec tous les champs requis
        prof_profile_data = {
            'profile': profile,
            'establishment_type': establishment_type,
            'establishment_name': self.cleaned_data['establishment_name'],
            'siret_or_rccm': self.cleaned_data['siret_or_rccm'],
            'legal_representative': f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}",
            'legal_phone': self.cleaned_data['legal_phone'],
            'establishment_address': self.cleaned_data['establishment_address'],
            'establishment_city': self.cleaned_data['establishment_city'],
            'establishment_postal_code': self.cleaned_data.get('establishment_postal_code', ''),
            'number_of_rooms': self.cleaned_data['number_of_rooms'],
            'number_of_floors': self.cleaned_data.get('number_of_floors'),
            'website': self.cleaned_data.get('website', ''),
            'legal_document': self.cleaned_data['legal_document'],
            'establishment_photo': process_image(self.cleaned_data['establishment_photo']),
        }
        
        # Utiliser get_or_create avec les defaults pour créer avec tous les champs requis
        prof_profile, created = ProfessionalProfile.objects.get_or_create(
            profile=profile,
            defaults=prof_profile_data
        )
        
        # Si l'objet existait déjà, mettre à jour les champs
        if not created:
            for key, value in prof_profile_data.items():
                if key != 'profile':
                    setattr(prof_profile, key, value)
        
        if commit:
            prof_profile.save()
        
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
            'photo_couverture',
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
            'photo_couverture': 'Photo de couverture',
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
        # Process uploaded images
        photo = self.cleaned_data.get('photo_profil')
        if photo:
            profile.photo_profil = process_image(photo)
        cover = self.cleaned_data.get('photo_couverture')
        if cover:
            profile.photo_couverture = process_image(cover, size=(1200, 400))
        if commit:
            profile.save()
        return profile

