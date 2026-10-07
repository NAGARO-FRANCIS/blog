import os

def rd(p):
    return open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')

def wr(p, s):
    open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', '\r\n'))

def remplacer(s, old, new, nom):
    if s.count(old) != 1:
        raise SystemExit(f"STOP : bloc introuvable ({nom}). Rien n'a été modifié dans ce fichier.")
    return s.replace(old, new)

if not os.path.exists('messagerie/views.py'):
    raise SystemExit("Lance ce script depuis C:\\projet\\pro\\ivoire")

# ---- views.py ----
p = 'messagerie/views.py'
s = rd(p)
if '_trouver_ou_creer_conversation' not in s:
    s = remplacer(s,
        "    conversations = Conversation.objects.filter(\n        participants=request.user\n    ).prefetch_related('participants', 'messages').order_by('-updated_at')",
        "    conversations = Conversation.objects.filter(\n        participationconversation__user=request.user,\n        participationconversation__masquee=False,\n    ).prefetch_related('participants', 'messages').order_by('-updated_at')",
        "liste")
    start = s.index("            # Créer ou récupérer la conversation\n")
    end = s.index("            message_type = 'text'\n")
    bloc = '''            # Créer ou récupérer la conversation (une par paire, et par annonce de colocation)
            if annonce and annonce_type == 'colocation':
                sujet = f"Colocation à {annonce.ville}"
                if annonce.quartier:
                    sujet += f" - {annonce.quartier}"
                conversation = _trouver_ou_creer_conversation(
                    request.user, destinataire, annonce_coloc=annonce, sujet=sujet
                )
            elif annonce:
                sujet = f"Logement à {annonce.ville}"
                if getattr(annonce, 'quartier', None):
                    sujet += f" - {annonce.quartier}"
                conversation = _trouver_ou_creer_conversation(
                    request.user, destinataire, sujet=sujet
                )
            else:
                conversation = _trouver_ou_creer_conversation(request.user, destinataire)

'''
    s = s[:start] + bloc + s[end:]
    s = remplacer(s,
        "            from accounts.notification_service import message_sent\n",
        "            ParticipationConversation.objects.filter(conversation=conversation).update(masquee=False)\n            from accounts.notification_service import message_sent\n",
        "notification")
    start = s.index("    # Retirer l'utilisateur de la conversation\n")
    end = s.index('    django_messages.success(request, "Conversation supprimée.")')
    s = s[:start] + "    # Suppression douce : masquée pour cet utilisateur seulement\n    ParticipationConversation.objects.filter(\n        conversation=conversation, user=request.user\n    ).update(masquee=True)\n\n" + s[end:]
    helper = '''def _trouver_ou_creer_conversation(user, destinataire, annonce_coloc=None, sujet=''):
    """Une conversation par paire d'utilisateurs (et par annonce de colocation)."""
    qs = Conversation.objects.filter(participants=user).filter(participants=destinataire)
    if annonce_coloc is not None:
        qs = qs.filter(annonce=annonce_coloc)
    else:
        qs = qs.filter(annonce__isnull=True)
    conversation = qs.first()
    if conversation is None:
        conversation = Conversation.objects.create(sujet=sujet, annonce=annonce_coloc)
        ParticipationConversation.objects.get_or_create(conversation=conversation, user=user)
        ParticipationConversation.objects.get_or_create(conversation=conversation, user=destinataire)
    return conversation


'''
    s = remplacer(s, "@login_required\ndef mes_conversations(request):",
                  helper + "@login_required\ndef mes_conversations(request):", "helper")
    wr(p, s)

# ---- context_processors.py (messages non lus) ----
p = 'ivoire/context_processors.py'
s = rd(p)
if 'masquee' not in s:
    s = remplacer(s,
        "        conversations = Conversation.objects.filter(\n            participants=request.user\n        ).prefetch_related('messages')",
        "        conversations = Conversation.objects.filter(\n            participationconversation__user=request.user,\n            participationconversation__masquee=False,\n        ).prefetch_related('messages')",
        "context_processors")
    wr(p, s)

# ---- settings.py (context processor i18n) ----
p = 'ivoire/settings.py'
s = rd(p)
if 'context_processors.i18n' not in s:
    s = remplacer(s,
        "                'ivoire.context_processors.unread_messages_count',\n",
        "                'ivoire.context_processors.unread_messages_count',\n                'django.template.context_processors.i18n',\n",
        "settings")
    wr(p, s)

print("Correctif appliqué.")