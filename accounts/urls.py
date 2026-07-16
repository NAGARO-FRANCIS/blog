from django.urls import include, path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    inscription, inscription_individu, inscription_individu_form, inscription_residence, inscription_hotel,
    inscription_pending, activate_account,
    dashboard, dashboard_individu, dashboard_residence, dashboard_hotel,
    profil, edit_profil, verification_docs, upload_document
)
from .subscription_views import (
    subscribe, unsubscribe, is_subscribed, get_subscriber_count,
    notifications_list, mark_as_read, unread_notifications_count,
    mark_all_as_read, notifications_api
)

app_name = 'accounts'

urlpatterns = [
    # Inscription
    path('inscription/', inscription, name='inscription'),
    path('inscription/individu/', inscription_individu, name='inscription_individu'),
    path('inscription/individu/formulaire/', inscription_individu_form, name='inscription_individu_form'),
    path('inscription/residence/', inscription_residence, name='inscription_residence'),
    path('inscription/hotel/', inscription_hotel, name='inscription_hotel'),
    path('inscription/pending/', inscription_pending, name='inscription_pending'),
    path('activer/<uidb64>/<token>/', activate_account, name='activate_account'),
    
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
    
    # Abonnements & Notifications
    path('subscribe/<int:user_id>/', subscribe, name='subscribe'),
    path('unsubscribe/<int:user_id>/', unsubscribe, name='unsubscribe'),
    path('is-subscribed/<int:user_id>/', is_subscribed, name='is_subscribed'),
    path('subscriber-count/<int:user_id>/', get_subscriber_count, name='subscriber_count'),
    path('notifications/', notifications_list, name='notifications'),
    path('notifications/mark-as-read/<int:notification_id>/', mark_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-as-read/', mark_all_as_read, name='mark_all_notifications_as_read'),
    path('notifications/unread-count/', unread_notifications_count, name='unread_notifications_count'),
    path('api/notifications/', notifications_api, name='notifications_api'),

    # Authentication
    path('password_reset/', auth_views.PasswordResetView.as_view(
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),
    path('', include('django.contrib.auth.urls')),
]
