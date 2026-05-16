from django.urls import include, path
from .views import (
    inscription, inscription_individu, inscription_individu_form, inscription_residence, inscription_hotel,
    dashboard, dashboard_individu, dashboard_residence, dashboard_hotel,
    profil, edit_profil, verification_docs, upload_document
)

app_name = 'accounts'

urlpatterns = [
    # Inscription
    path('inscription/', inscription, name='inscription'),
    path('inscription/individu/', inscription_individu, name='inscription_individu'),
    path('inscription/individu/formulaire/', inscription_individu_form, name='inscription_individu_form'),
    path('inscription/residence/', inscription_residence, name='inscription_residence'),
    path('inscription/hotel/', inscription_hotel, name='inscription_hotel'),
    
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/individu/', dashboard_individu, name='dashboard_individu'),
    path('dashboard/residence/', dashboard_residence, name='dashboard_residence'),
    path('dashboard/hotel/', dashboard_hotel, name='dashboard_hotel'),
    
    # Profil
    path('profil/', profil, name='profil'),
    path('profil/editer/', edit_profil, name='edit_profil'),
    
    # Vérification
    path('verification-docs/', verification_docs, name='verification_docs'),
    path('upload-document/', upload_document, name='upload_document'),
    
    # Authentication
    path('', include('django.contrib.auth.urls')),
]
