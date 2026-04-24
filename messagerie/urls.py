from django.urls import path
from .views import (
    mes_conversations,
    conversation_detail,
    envoyer_message,
    demarrer_conversation,
    supprimer_conversation
)

app_name = 'messagerie'

urlpatterns = [
    path('', mes_conversations, name='mes_conversations'),
    path('conversation/<int:conversation_id>/', conversation_detail, name='conversation_detail'),
    path('envoyer/', envoyer_message, name='envoyer_message'),
    path('envoyer/<str:annonce_type>/<int:annonce_id>/', envoyer_message, name='envoyer_message_annonce'),
    path('demarrer/<int:user_id>/', demarrer_conversation, name='demarrer_conversation'),
    path('supprimer/<int:conversation_id>/', supprimer_conversation, name='supprimer_conversation'),
]
