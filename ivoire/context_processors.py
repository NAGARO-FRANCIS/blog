from messagerie.models import Message, Conversation


def unread_messages_count(request):
    """
    Context processor pour ajouter le nombre de messages non lus à tous les templates
    """
    unread_count = 0
    
    if request.user.is_authenticated:
        # Compter le nombre total de messages non lus pour cet utilisateur
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('messages')
        
        for conversation in conversations:
            unread_count += conversation.get_unread_count(request.user)
    
    return {
        'unread_messages_count': unread_count,
    }
