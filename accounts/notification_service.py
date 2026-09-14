import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


logger = logging.getLogger(__name__)


def _phone(user):
    try:
        return user.profile.telephone
    except Exception:
        return ''


def _send_sms(user, message):
    phone = _phone(user)
    if not phone:
        return
    if getattr(settings, 'SMS_BACKEND', 'console') in ('', 'console'):
        logger.info('[SMS -> %s] %s', phone, message)
        return
    logger.warning('SMS_BACKEND configuré mais aucun fournisseur SMS n’est intégré.')


def notify_user(user, notification_type, title, message, actor=None,
                listing_id=None, reservation_id=None, payment_id=None,
                email_subject=None, sms_message=None):
    """Crée une notification in-app et envoie les canaux configurés."""
    if not user:
        return None
    notification = Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        actor=actor,
        related_listing_id=listing_id,
        related_reservation_id=reservation_id,
        related_payment_id=payment_id,
    )
    if user.email and email_subject:
        send_mail(email_subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    if sms_message:
        _send_sms(user, sms_message)
    return notification


def reservation_created(reservation):
    owner = reservation.logement.proprietaire
    message = f'Nouvelle réservation pour « {reservation.logement.titre} », du {reservation.date_arrivee:%d/%m/%Y} au {reservation.date_depart:%d/%m/%Y}.'
    if owner:
        notify_user(owner, 'reservation', 'Nouvelle réservation', message,
                   listing_id=reservation.logement_id, reservation_id=reservation.id,
                   email_subject='Nouvelle réservation Ivoire Connect')
    if reservation.client_user:
        notify_user(reservation.client_user, 'reservation', 'Réservation enregistrée',
                    f'Votre réservation de « {reservation.logement.titre} » est enregistrée.',
                    listing_id=reservation.logement_id, reservation_id=reservation.id,
                    email_subject='Votre réservation Ivoire Connect est enregistrée')


def reservation_confirmed(reservation):
    if not reservation.client_user:
        return
    message = f'Votre réservation de « {reservation.logement.titre} » est confirmée.'
    notify_user(reservation.client_user, 'reservation', 'Réservation confirmée', message,
                listing_id=reservation.logement_id, reservation_id=reservation.id,
                email_subject='Votre réservation est confirmée',
                sms_message=f'Votre réservation Ivoire Connect est confirmée. {reservation.logement.titre}')


def payment_received(payment):
    reservation = payment.reservation
    recipient = reservation.client_user or reservation.logement.proprietaire
    notify_user(recipient, 'payment', 'Paiement reçu',
                f'Paiement de {payment.montant:.0f} FCFA reçu pour « {reservation.logement.titre} ».',
                listing_id=reservation.logement_id, reservation_id=reservation.id,
                payment_id=payment.id, email_subject='Paiement reçu Ivoire Connect')


def favorite_added(favorite):
    owner = favorite.logement.proprietaire
    if owner and owner != favorite.utilisateur:
        notify_user(owner, 'favorite', 'Votre logement a été ajouté aux favoris',
                    f'{favorite.utilisateur.get_full_name() or favorite.utilisateur.username} a ajouté « {favorite.logement.titre} » à ses favoris.',
                    actor=favorite.utilisateur, listing_id=favorite.logement_id)


def message_sent(message):
    if not message.conversation:
        return
    for recipient in message.conversation.participants.exclude(id=message.expediteur_id):
        notify_user(recipient, 'message', 'Nouveau message',
                    f'{message.expediteur.get_full_name() or message.expediteur.username} vous a envoyé un message.',
                    actor=message.expediteur)