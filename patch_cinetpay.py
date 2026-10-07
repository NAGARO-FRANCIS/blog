import os


def rd(p):
    return open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')


def wr(p, s):
    open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', '\r\n'))


def remplacer(s, old, new, nom):
    if s.count(old) != 1:
        raise SystemExit(f"STOP : bloc introuvable ({nom}). Rien n'a été modifié dans ce fichier.")
    return s.replace(old, new)


if not os.path.exists('logement/cinetpay_paiement.py'):
    raise SystemExit("Crée d'abord le fichier logement/cinetpay_paiement.py")

# ---- models.py : champ pour le jeton de notification ----
p = 'logement/models.py'
s = rd(p)
if 'cinetpay_notify_token' not in s:
    s = remplacer(s,
        '        help_text="payment_token renvoyé par CinetPay à l\'initialisation"\n    )\n',
        '        help_text="payment_token renvoyé par CinetPay à l\'initialisation"\n    )\n'
        '    cinetpay_notify_token = models.CharField(\n'
        '        max_length=255,\n'
        '        blank=True,\n'
        '        help_text="notify_token renvoyé par CinetPay (vérifie les notifications)"\n'
        '    )\n',
        "models")
    wr(p, s)

# ---- urls.py : notification et page de retour ----
p = 'logement/urls.py'
s = rd(p)
if 'cinetpay_notify' not in s:
    s = remplacer(s,
        "\napp_name = 'logement'\n",
        "from .cinetpay_paiement import cinetpay_notify, cinetpay_retour\n\napp_name = 'logement'\n",
        "urls import")
    s = remplacer(s,
        "    path('reservation/<int:reservation_id>/paiement/', paiement_reservation, name='paiement'),\n",
        "    path('reservation/<int:reservation_id>/paiement/', paiement_reservation, name='paiement'),\n"
        "    path('reservation/<int:reservation_id>/paiement/retour/', cinetpay_retour, name='cinetpay_retour'),\n"
        "    path('paiement/cinetpay/notify/', cinetpay_notify, name='cinetpay_notify'),\n",
        "urls paths")
    wr(p, s)

# ---- views.py : Mobile Money passe par CinetPay ----
p = 'logement/views.py'
s = rd(p)
if 'initier_paiement' not in s:
    s = remplacer(s,
        "            if payment_method == 'mouv':\n                # MOUV - Mobile Money\n",
        "            if payment_method in ('mobile_money', 'mouv', 'orange', 'wave'):\n"
        "                # Mobile Money (Orange, MTN, Moov, Wave) via la page sécurisée CinetPay\n"
        "                import logging\n"
        "                from cinetpay import CinetPayError\n"
        "                from .cinetpay_paiement import CinetPayNonConfigure, initier_paiement\n"
        "\n"
        "                if paiement.statut == 'completed':\n"
        "                    return JsonResponse({\n"
        "                        'success': True,\n"
        "                        'message': _('Cette réservation est déjà payée.'),\n"
        "                        'redirect_url': f'/logement/reservation/{reservation.id}/confirmation/'\n"
        "                    })\n"
        "                try:\n"
        "                    url_paiement = initier_paiement(paiement)\n"
        "                except CinetPayNonConfigure:\n"
        "                    return JsonResponse({\n"
        "                        'success': False,\n"
        "                        'message': _(\"Le paiement en ligne n'est pas encore configuré.\")\n"
        "                    }, status=503)\n"
        "                except CinetPayError:\n"
        "                    logging.getLogger(__name__).exception('CinetPay : initialisation impossible')\n"
        "                    return JsonResponse({\n"
        "                        'success': False,\n"
        "                        'message': _(\"Impossible d'initialiser le paiement. Réessayez dans un instant.\")\n"
        "                    }, status=502)\n"
        "                return JsonResponse({\n"
        "                    'success': True,\n"
        "                    'message': _('Redirection vers la page de paiement sécurisée...'),\n"
        "                    'redirect_url': url_paiement\n"
        "                })\n"
        "\n"
        "            elif payment_method == 'mouv_ancien':\n"
        "                # Ancien code MOUV (désormais inutilisé)\n",
        "views")
    wr(p, s)

print("Correctif CinetPay appliqué.")