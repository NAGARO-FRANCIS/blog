from django.urls import path
from . import views


app_name = "adminpanel"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("utilisateurs/", views.users, name="users"),
    path("utilisateurs/<int:user_id>/activer/", views.activate_user, name="activate_user"),
    path("logements/", views.logements, name="logements"),
    path("colocations/", views.colocations, name="colocations"),
    path("hotels-residences/", views.hotels_residences, name="hotels_residences"),
    path("hotels-residences/<int:establishment_id>/verification/", views.establishment_review, name="establishment_review"),
    path("hotels-residences/<int:establishment_id>/documents/<str:document_kind>/", views.establishment_document_file, name="establishment_document_file"),
    path("hotels-residences/<int:establishment_id>/approuver/", views.approve_establishment, name="approve_establishment"),
    path("reservations/", views.reservations, name="reservations"),
    path("finance/", views.finance, name="finance"),
    path("verifications/", views.verifications, name="verifications"),
    path("verifications/dossier/<int:profile_id>/", views.verification_dossier, name="verification_dossier"),
    path("verifications/document/<int:document_id>/fichier/", views.verification_document_file, name="verification_document_file"),
    path("verifications/<int:document_id>/approuver/", views.approve_document, name="approve_document"),
    path("verifications/<int:document_id>/rejeter/", views.reject_document, name="reject_document"),
    path("avis/", views.avis, name="avis"),
    path("avis/<int:avis_id>/visibilite/", views.toggle_avis_visibility, name="toggle_avis_visibility"),
    path("signalements/", views.signalements, name="signalements"),
    path("signalements/<int:signalement_id>/traiter/", views.traiter_signalement, name="traiter_signalement"),
    path("notifications/", views.notifications, name="notifications"),
    path("statistiques/", views.statistiques, name="statistiques"),
    path("parametres/", views.parametres, name="parametres"),
]