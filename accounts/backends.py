# accounts/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification qui accepte soit l'email soit le nom d'utilisateur
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        username = username.strip()
        users = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        )
        if users.count() != 1:
            return None
        user = users.get()

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
