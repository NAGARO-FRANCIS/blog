from django.urls import path
from .views import (
    home, listings_all_types, choisir_type_annonce, ajouter_logement, modifier_logement, supprimer_logement,
    mes_logements, gestion_logements,
    mes_reservations, calendrier_reservations, mes_paiements,
    mes_clients, avis_clients, statistiques_professionnel,
    detail_logement, toggle_favori, mes_favoris, reserver_logement, paiement_reservation, confirmation_reservation
)

app_name = 'logement'

urlpatterns = [
    path('', home, name='home'),
    path('all-listings/', listings_all_types, name='listings_all_types'),
    
    # Publication d'annonce
    path('publier/', choisir_type_annonce, name='choisir_type_annonce'),
    path('ajouter/', ajouter_logement, name='ajouter_logement'),
    path('<int:id>/modifier/', modifier_logement, name='modifier_logement'),
    path('<int:id>/supprimer/', supprimer_logement, name='supprimer_logement'),
    path('mes-logements/', mes_logements, name='mes_logements'),
    path('gestion/', gestion_logements, name='gestion_logements'),
    
    # Gestion des réservations
    path('reservations/', mes_reservations, name='mes_reservations'),
    path('calendrier/', calendrier_reservations, name='calendrier_reservations'),
    
    # Gestion des paiements
    path('paiements/', mes_paiements, name='mes_paiements'),
    
    # Gestion des clients
    path('clients/', mes_clients, name='mes_clients'),
    
    # Avis et statistiques
    path('avis/', avis_clients, name='avis_clients'),
    path('statistiques/', statistiques_professionnel, name='statistiques'),
    
    # Favoris (doit venir AVANT les routes avec <int:id>/)
    path('favoris/', mes_favoris, name='mes_favoris'),
    
    # Détail, favoris et réservation (routes dynamiques en dernier)
    path('<int:id>/', detail_logement, name='detail_logement'),
    path('<int:id>/toggle-favori/', toggle_favori, name='toggle_favori'),
    path('<int:id>/reserver/', reserver_logement, name='reserver_logement'),
    path('reservation/<int:reservation_id>/paiement/', paiement_reservation, name='paiement'),
    path('reservation/<int:reservation_id>/confirmation/', confirmation_reservation, name='confirmation_reservation'),
]