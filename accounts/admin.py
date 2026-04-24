from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'ville', 'profession', 'verified']
    list_filter = ['role', 'verified', 'sexe']
    search_fields = ['user__username', 'user__email', 'profession', 'ville']
    readonly_fields = ['user']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('telephone', 'date_naissance', 'sexe')
        }),
        ('Informations du profil', {
            'fields': ('role', 'ville', 'quartier', 'profession', 'photo_profil')
        }),
        ('Vérification', {
            'fields': ('verified',),
            'description': 'Cochez pour activer les permissions de publication'
        }),
    )
    
    actions = ['make_verified', 'make_unverified']
    
    def make_verified(self, request, queryset):
        queryset.update(verified=True)
    make_verified.short_description = "✓ Vérifier les profils sélectionnés"
    
    def make_unverified(self, request, queryset):
        queryset.update(verified=False)
    make_unverified.short_description = "✗ Révoquer la vérification"
