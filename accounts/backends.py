# accounts/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification qui accepte soit l'email soit le nom d'utilisateur
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Chercher l'utilisateur par email ou username
            user = User.objects.get(email=username) if '@' in username else User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        # Vérifier le mot de passe
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
