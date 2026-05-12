from django.urls import path
from .views import home, ajouter_logement

app_name = 'logement'

urlpatterns = [
    path('', home, name='home'),
    path('ajouter/', ajouter_logement, name='ajouter_logement'),
]