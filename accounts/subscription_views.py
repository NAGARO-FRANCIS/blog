from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import Subscription, Notification


@login_required
@require_POST
def subscribe(request, user_id):
    """S'abonner à un utilisateur"""
    creator = get_object_or_404(User, id=user_id)
    
    # Vérifier qu'on ne s'abonne pas à soi-même
    if request.user == creator:
        return JsonResponse({'success': False, 'message': 'Vous ne pouvez pas vous abonner à vous-même'}, status=400)
    
    subscription, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        creator=creator
    )
    
    if not created:
        # Réactiver l'abonnement s'il était désactivé
        if not subscription.is_active:
            subscription.is_active = True
            subscription.save()
            created = True
    
    if created:
        # Créer une notification pour le créateur
        Notification.create_subscription_notification(request.user, creator)
    
    return JsonResponse({
        'success': True,
        'message': 'Vous êtes maintenant abonné',
        'is_subscribed': True,
        'subscriber_count': subscription.subscriber_count
    })


@login_required
@require_POST
def unsubscribe(request, user_id):
    """Se désabonner d'un utilisateur"""
    creator = get_object_or_404(User, id=user_id)
    
    subscription = get_object_or_404(Subscription, subscriber=request.user, creator=creator)
    subscription.is_active = False
    subscription.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Vous avez été désabonné',
        'is_subscribed': False,
        'subscriber_count': Subscription.objects.filter(creator=creator, is_active=True).count()
    })


@login_required
def is_subscribed(request, user_id):
    """Vérifier si l'utilisateur est abonné"""
    creator = get_object_or_404(User, id=user_id)
    
    try:
        subscription = Subscription.objects.get(subscriber=request.user, creator=creator, is_active=True)
        is_subscribed = True
    except Subscription.DoesNotExist:
        is_subscribed = False
    
    subscriber_count = Subscription.objects.filter(creator=creator, is_active=True).count()
    
    return JsonResponse({
        'is_subscribed': is_subscribed,
        'subscriber_count': subscriber_count
    })


@login_required
def get_subscriber_count(request, user_id):
    """Obtenir le nombre d'abonnés"""
    creator = get_object_or_404(User, id=user_id)
    
    subscriber_count = Subscription.objects.filter(creator=creator, is_active=True).count()
    
    return JsonResponse({
        'subscriber_count': subscriber_count
    })


@login_required
def notifications_list(request):
    """Afficher la liste des notifications"""
    notifications = Notification.objects.filter(recipient=request.user).prefetch_related('actor')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'accounts/notifications.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'success': True})


@login_required
def unread_notifications_count(request):
    """Obtenir le nombre de notifications non lues"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    return JsonResponse({
        'unread_count': count
    })


@login_required
@require_POST
def mark_all_as_read(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return JsonResponse({'success': True})


@login_required
def notifications_api(request):
    """API pour obtenir les notifications non lues (pour AJAX)"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).values('id', 'title', 'message', 'notification_type', 'created_at', 'actor__username')[:10]
    
    return JsonResponse({
        'notifications': list(notifications),
        'count': len(list(notifications))
    })
