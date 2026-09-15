from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import AppelSession, AppelSignal, Conversation, Message, ParticipationConversation
import json
from colocation.models import ColocationAnnonce
from logement.models import Logement


@login_required
def mes_conversations(request):
    """Affiche toutes les conversations de l'utilisateur"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'messages').order_by('-updated_at')

    # Ajouter des informations supplémentaires pour chaque conversation
    conversations_with_info = []
    for conv in conversations:
        other_participant = conv.get_other_participant(request.user)
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)

        conversations_with_info.append({
            'conversation': conv,
            'other_participant': other_participant,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    return render(request, 'messagerie/mes_messages.html', {
        'conversations': conversations_with_info
    })


@login_required
def conversation_detail(request, conversation_id):
    """Affiche les détails d'une conversation spécifique"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        participants=request.user
    )

    # Marquer les messages comme lus
    conversation.mark_as_read(request.user)

    # Récupérer tous les messages de la conversation
    messages = conversation.messages.select_related('expediteur').order_by('created_at')

    other_participant = conversation.get_other_participant(request.user)

    return render(request, 'messagerie/conversation_detail.html', {
        'conversation': conversation,
        'conversation_messages': messages,
        'other_participant': other_participant,
    })


def _conversation_for_user(request, conversation_id):
    return get_object_or_404(Conversation, pk=conversation_id, participants=request.user)


@login_required
@require_POST
def demarrer_appel(request):
    conversation = _conversation_for_user(request, request.POST.get('conversation_id'))
    callee = conversation.get_other_participant(request.user)
    if not callee:
        return JsonResponse({'error': 'Aucun destinataire.'}, status=400)
    AppelSession.objects.filter(conversation=conversation, status__in=['ringing', 'active']).update(status='ended')
    media_type = request.POST.get('media_type', 'video')
    if media_type not in ('audio', 'video'):
        return JsonResponse({'error': 'Type d’appel invalide.'}, status=400)
    session = AppelSession.objects.create(
        conversation=conversation,
        caller=request.user,
        callee=callee,
        media_type=media_type,
    )
    return JsonResponse({'session_id': session.id})


@login_required
@require_GET
def appels_actifs(request):
    conversation = _conversation_for_user(request, request.GET.get('conversation_id'))
    session = AppelSession.objects.filter(
        conversation=conversation,
        status__in=['ringing', 'active'],
    ).exclude(caller=request.user).select_related('caller').first()
    if not session:
        return JsonResponse({'call': None})
    return JsonResponse({'call': {
        'id': session.id,
        'media_type': session.media_type,
        'caller': session.caller.get_full_name() or session.caller.username,
    }})


@login_required
@require_GET
def etat_appel(request, session_id):
    session = get_object_or_404(AppelSession, pk=session_id)
    if request.user not in (session.caller, session.callee):
        return JsonResponse({'error': 'Acces refuse.'}, status=403)
    after_id = int(request.GET.get('after', 0))
    signals = AppelSignal.objects.filter(session=session, id__gt=after_id).exclude(sender=request.user).order_by('id')
    return JsonResponse({
        'status': session.status,
        'signals': [{'id': signal.id, 'kind': signal.kind, 'payload': signal.payload} for signal in signals],
    })


@login_required
@require_POST
def signaler_appel(request, session_id):
    session = get_object_or_404(AppelSession, pk=session_id)
    if request.user not in (session.caller, session.callee) or session.status == 'ended':
        return JsonResponse({'error': 'Appel indisponible.'}, status=403)
    data = json.loads(request.body or '{}')
    kind = data.get('kind')
    if kind not in ('offer', 'answer', 'candidate', 'hold'):
        return JsonResponse({'error': 'Signal invalide.'}, status=400)
    AppelSignal.objects.create(session=session, sender=request.user, kind=kind, payload=json.dumps(data.get('payload')))
    if kind == 'answer':
        session.status = 'active'
        session.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def terminer_appel(request, session_id):
    session = get_object_or_404(AppelSession, pk=session_id)
    if request.user not in (session.caller, session.callee):
        return JsonResponse({'error': 'Acces refuse.'}, status=403)
    session.status = 'ended'
    session.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'ok': True})


@login_required
def envoyer_message(request, annonce_id=None, annonce_type=None):
    """
    Envoie un message à propos d'une annonce ou continue une conversation existante.
    Restrictions Facebook/WhatsApp :
    - Un utilisateur ne peut pas s'envoyer de message à lui-même
    - Les messages sont organisés en conversations
    """
    annonce = None
    destinataire = None

    # Si on vient d'une annonce spécifique
    if annonce_id and annonce_type:
        if annonce_type == 'colocation':
            annonce = get_object_or_404(ColocationAnnonce, pk=annonce_id)
        elif annonce_type == 'logement':
            annonce = get_object_or_404(Logement, pk=annonce_id)

        if annonce:
            destinataire = annonce.proprietaire

            # Vérifier que l'utilisateur n'essaie pas de se contacter lui-même
            if destinataire == request.user:
                django_messages.error(request, "Vous ne pouvez pas envoyer de message à votre propre annonce.")
                return redirect('colocation:colocation_home' if annonce_type == 'colocation' else 'home')

    # Si c'est une réponse à un message existant (conversation_id dans POST)
    conversation_id = request.POST.get('conversation_id')
    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            pk=conversation_id,
            participants=request.user
        )
        destinataire = conversation.get_other_participant(request.user)

    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        attachment = request.FILES.get('attachment')

        if not contenu and not attachment:
            django_messages.error(request, "Le message ne peut pas être vide.")
            return redirect(request.META.get('HTTP_REFERER', 'messagerie:mes_conversations'))

        try:
            # Créer ou récupérer la conversation
            if annonce:
                # Conversation liée à une annonce.
                # Les conversations sont stockées avec une relation vers des annonces de colocation,
                # donc pour les logements on crée une conversation simple avec un sujet adapté.
                if annonce_type == 'colocation':
                    sujet = f"Colocation à {annonce.ville}"
                    if annonce.quartier:
                        sujet += f" - {annonce.quartier}"

                    conversation, created = Conversation.objects.get_or_create(
                        annonce=annonce,
                        defaults={'sujet': sujet}
                    )
                    if created:
                        conversation.participants.add(request.user, destinataire)
                else:
                    sujet = f"Logement à {annonce.ville}"
                    if getattr(annonce, 'quartier', None):
                        sujet += f" - {annonce.quartier}"

                    conversation = Conversation.objects.filter(
                        participants=request.user
                    ).filter(
                        participants=destinataire
                    ).filter(
                        annonce__isnull=True
                    ).first()

                    if conversation:
                        created = False
                    else:
                        conversation = Conversation.objects.create(sujet=sujet)
                        conversation.participants.add(request.user, destinataire)
                        created = True
            else:
                # Conversation directe (sans annonce)
                # Chercher une conversation existante entre ces deux utilisateurs
                conversation = Conversation.objects.filter(
                    participants=request.user
                ).filter(
                    participants=destinataire
                ).filter(
                    annonce__isnull=True
                ).first()

                if conversation:
                    created = False
                else:
                    conversation = Conversation.objects.create()
                    conversation.participants.add(request.user, destinataire)
                    created = True

            message_type = 'text'
            if attachment:
                forced_type = (request.POST.get('message_type') or '').strip().lower()
                content_type = (getattr(attachment, 'content_type', '') or '').lower()
                filename = (getattr(attachment, 'name', '') or '').lower()

                if forced_type in {'audio', 'video', 'image', 'file'}:
                    message_type = forced_type
                elif content_type.startswith('audio/') or filename.endswith(('.ogg', '.mp3', '.wav', '.m4a', '.aac', '.webm')):
                    message_type = 'audio'
                elif content_type.startswith('video/') or filename.endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4v')):
                    message_type = 'video'
                elif content_type.startswith('image/') or filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    message_type = 'image'
                else:
                    message_type = 'file'

            # Créer le message
            message = Message.objects.create(
                conversation=conversation,
                expediteur=request.user,
                contenu=contenu or '',
                attachment=attachment,
                message_type=message_type,
            )
            from accounts.notification_service import message_sent
            message_sent(message)

            django_messages.success(request, "Message envoyé avec succès.")
            return redirect('messagerie:conversation_detail', conversation_id=conversation.id)

        except ValidationError as e:
            django_messages.error(request, str(e))
        except Exception as e:
            django_messages.error(request, "Une erreur est survenue lors de l'envoi du message.")

    # Contexte pour le template
    context = {}
    if annonce:
        context['annonce'] = annonce
        context['destinataire'] = destinataire
    elif conversation_id:
        conversation = get_object_or_404(
            Conversation,
            pk=conversation_id,
            participants=request.user
        )
        context['conversation'] = conversation
        context['destinataire'] = conversation.get_other_participant(request.user)
    
    # Si on a déjà identifié un destinataire, l'ajouter au contexte
    if destinataire and 'destinataire' not in context:
        context['destinataire'] = destinataire

    return render(request, 'messagerie/envoyer_message.html', context)


@login_required
def demarrer_conversation(request, user_id):
    """Démarre une nouvelle conversation avec un utilisateur"""
    destinataire = get_object_or_404(User, pk=user_id)

    # Vérifier que ce n'est pas soi-même
    if destinataire == request.user:
        django_messages.error(request, "Vous ne pouvez pas démarrer une conversation avec vous-même.")
        return redirect('accounts:profil', username=request.user.username)

    # Vérifier si une conversation existe déjà
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=destinataire
    ).filter(
        annonce__isnull=True
    ).first()

    if conversation:
        return redirect('messagerie:conversation_detail', conversation_id=conversation.id)

    # Rediriger vers le formulaire d'envoi de message
    return redirect('messagerie:envoyer_message')


@login_required
def supprimer_conversation(request, conversation_id):
    """Supprime une conversation (désactive la participation)"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        participants=request.user
    )

    # Retirer l'utilisateur de la conversation
    conversation.participants.remove(request.user)

    # Si plus de participants, supprimer la conversation
    if conversation.participants.count() == 0:
        conversation.delete()

    django_messages.success(request, "Conversation supprimée.")
    return redirect('messagerie:mes_conversations')
