# accounts/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification qui accepte soit l'email soit le nom d'utilisateur
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            # Chercher l'utilisateur par email ou username
            user = User.objects.get(email=username) if '@' in username else User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # Vérifier le mot de passe
        if not user.check_password(password):
            return None

        if not user.is_active:
            profile = getattr(user, 'profile', None)
            if profile and profile.activation_token:
                user.is_active = True
                user.save(update_fields=['is_active'])
                profile.activation_token = ''
                profile.activation_token_created_at = None
                profile.save(update_fields=['activation_token', 'activation_token_created_at'])
            else:
                return None

        if self.user_can_authenticate(user):
            return user

        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
