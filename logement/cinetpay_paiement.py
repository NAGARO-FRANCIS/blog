"""
Paiement Mobile Money via CinetPay (API v1) : initialisation, notification (webhook)
et page de retour. La réservation n'est marquée "payée" qu'après vérification
du statut directement auprès de CinetPay.
"""
import json
import logging
import os
import time
from decimal import ROUND_CEILING

from cinetpay import (
    CinetPayClient,
    ClientConfig,
    CountryCredentials,
    PaymentRequest,
    parse_notification,
    verify_notification,
)
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Paiement, Reservation

logger = logging.getLogger(__name__)

PAYS = 'CI'
_client = None


class CinetPayNonConfigure(Exception):
    """Les clés CinetPay sont absentes du fichier .env."""


def get_client():
    global _client
    if _client is None:
        cle = os.getenv('CINETPAY_API_KEY_CI', '').strip()
        mot_de_passe = os.getenv('CINETPAY_API_PASSWORD_CI', '').strip()
        if not cle or not mot_de_passe:
            raise CinetPayNonConfigure('CINETPAY_API_KEY_CI / CINETPAY_API_PASSWORD_CI manquants')
        _client = CinetPayClient(ClientConfig(
            credentials={PAYS: CountryCredentials(api_key=cle, api_password=mot_de_passe)},
        ))
    return _client


def _site_url():
    return os.getenv('SITE_URL', 'http://127.0.0.1:8000').strip().rstrip('/')


def _noms(client_nom):
    parts = (client_nom or '').split()
    prenom = parts[0] if parts else 'Client'
    nom = ' '.join(parts[1:]) or prenom
    return (prenom if len(prenom) >= 2 else 'Client'), (nom if len(nom) >= 2 else 'Client')


def initier_paiement(paiement):
    """Crée la transaction chez CinetPay et renvoie l'URL de la page de paiement."""
    reservation = paiement.reservation
    prenom, nom = _noms(reservation.client_nom)
    montant = int(paiement.montant.to_integral_value(rounding=ROUND_CEILING))
    merchant_id = f"IVC{reservation.id}T{int(time.time())}"
    langue = 'en' if (get_language() or 'fr').startswith('en') else 'fr'
    logement = reservation.logement
    designation = f"{_('Réservation')} {getattr(logement, 'titre', None) or logement}"[:255]
    base = _site_url()

    requete = PaymentRequest(
        currency='XOF',
        merchant_transaction_id=merchant_id,
        amount=montant,
        lang=langue,
        designation=designation,
        client_email=reservation.client_email,
        client_first_name=prenom,
        client_last_name=nom,
        success_url=base + reverse('logement:cinetpay_retour', args=[reservation.id]),
        failed_url=base + reverse('logement:cinetpay_retour', args=[reservation.id]),
        notify_url=base + reverse('logement:cinetpay_notify'),
        channel='PUSH',
    )
    reponse = get_client().payment.initialize(requete, PAYS)

    paiement.methode = 'mobile_money'
    paiement.statut = 'pending'
    paiement.transaction_id = merchant_id
    paiement.cinetpay_payment_token = reponse.payment_token
    paiement.cinetpay_notify_token = reponse.notify_token
    paiement.save()
    return reponse.payment_url


@transaction.atomic
def appliquer_statut(paiement_id, statut):
    """Met à jour le paiement et la réservation. Sans danger si appelée plusieurs fois."""
    paiement = Paiement.objects.select_for_update().select_related('reservation').get(pk=paiement_id)
    if paiement.statut == 'completed':
        return paiement
    if statut == 'SUCCESS':
        paiement.statut = 'completed'
        paiement.completed_at = timezone.now()
        paiement.save(update_fields=['statut', 'completed_at'])
        reservation = paiement.reservation
        reservation.paye = True
        reservation.statut = 'confirmed'
        reservation.save(update_fields=['paye', 'statut', 'updated_at'])
    elif statut in ('FAILED', 'EXPIRED') and paiement.statut == 'pending':
        paiement.statut = 'failed'
        paiement.save(update_fields=['statut'])
    return paiement


def verifier_statut(paiement):
    """Interroge CinetPay (source de vérité) puis met à jour la base."""
    etat = get_client().payment.get_status(paiement.transaction_id, PAYS)
    if etat.merchant_transaction_id and etat.merchant_transaction_id != paiement.transaction_id:
        raise ValueError('Transaction CinetPay incohérente')
    return appliquer_statut(paiement.pk, etat.status)


@csrf_exempt
@require_POST
def cinetpay_notify(request):
    """Webhook appelé par CinetPay (doit être joignable depuis Internet)."""
    try:
        try:
            payload = parse_notification(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            payload = parse_notification(request.POST.dict())
    except (TypeError, ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    paiement = Paiement.objects.filter(transaction_id=payload.merchant_transaction_id).first()
    if paiement is None or not paiement.cinetpay_notify_token:
        return HttpResponse(status=404)
    if not verify_notification(paiement.cinetpay_notify_token, payload.notify_token):
        return HttpResponse(status=401)
    try:
        verifier_statut(paiement)
    except Exception:
        logger.exception('CinetPay : vérification impossible (paiement %s)', paiement.pk)
        return HttpResponse(status=500)  # CinetPay réessaiera
    return HttpResponse('OK')


@require_GET
def cinetpay_retour(request, reservation_id):
    """Page où CinetPay renvoie le client après le paiement."""
    from .views import _can_access_reservation

    reservation = get_object_or_404(Reservation, id=reservation_id)
    if not _can_access_reservation(request, reservation):
        return redirect('accounts:login' if not request.user.is_authenticated else 'logement:home')

    paiement = Paiement.objects.filter(reservation=reservation).first()
    if paiement and paiement.statut != 'completed' and paiement.transaction_id and paiement.cinetpay_notify_token:
        try:
            paiement = verifier_statut(paiement)
        except Exception:
            logger.exception('CinetPay : vérification au retour impossible (paiement %s)', paiement.pk)

    if paiement and paiement.statut == 'completed':
        messages.success(request, _('✅ Paiement confirmé. Votre réservation est validée.'))
        return redirect('logement:confirmation_reservation', reservation_id=reservation.id)
    if paiement and paiement.statut == 'failed':
        messages.error(request, _('❌ Le paiement a échoué ou a été annulé. Vous pouvez réessayer.'))
    else:
        messages.info(request, _('⏳ Paiement en cours de validation. La réservation sera confirmée dès réception.'))
    return redirect('logement:paiement', reservation_id=reservation.id)