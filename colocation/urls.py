# colocation/urls.py
from django.urls import path
from . import views

app_name = 'colocation'

urlpatterns = [
    path('', views.home, name='colocation_home'),
    path('annonces/', views.liste_annonces, name='liste_annonces'),
    path('annonces/<int:annonce_id>/', views.detail_annonce, name='detail_annonce'),
    path('publier/', views.publier_annonce, name='publier_annonce'),
    path('toggle-favori/<int:annonce_id>/', views.toggle_favori, name='toggle_favori'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
]