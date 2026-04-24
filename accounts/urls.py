from django.urls import include, path
from .views import inscription, profil, edit_profil

app_name = 'accounts'

urlpatterns = [
    path('inscription/', inscription, name='inscription'),
    path('profil/', profil, name='profil'),
    path('profil/editer/', edit_profil, name='edit_profil'),
    path('', include('django.contrib.auth.urls')),
]
