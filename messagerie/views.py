from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Conversation, Message, ParticipationConversation
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
        'messages': messages,
        'other_participant': other_participant,
    })


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

        if not contenu:
            django_messages.error(request, "Le message ne peut pas être vide.")
            return redirect(request.META.get('HTTP_REFERER', 'messagerie:mes_conversations'))

        try:
            # Créer ou récupérer la conversation
            if annonce:
                # Conversation liée à une annonce
                sujet = f"Colocation à {annonce.ville}"
                if annonce.quartier:
                    sujet += f" - {annonce.quartier}"
                
                conversation, created = Conversation.objects.get_or_create(
                    annonce=annonce,
                    defaults={'sujet': sujet}
                )
                if created:
                    # Ajouter les participants
                    conversation.participants.add(request.user, destinataire)
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

            # Créer le message
            message = Message.objects.create(
                conversation=conversation,
                expediteur=request.user,
                contenu=contenu
            )

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
