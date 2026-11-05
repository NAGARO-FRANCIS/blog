from messagerie.models import Message


def unread_messages_count(request):
    """
    Context processor pour ajouter le nombre de messages non lus à tous les templates
    """
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            conversation__participationconversation__user=request.user,
            conversation__participationconversation__masquee=False,
            lu=False,
        ).exclude(expediteur=request.user).count()
    
    return {
        'unread_messages_count': unread_count,
    }
