from django.contrib import admin
from .models import Logement, PhotoLogement


class PhotoLogementInline(admin.TabularInline):
    model = PhotoLogement
    extra = 1
    fields = ['image', 'alt_text', 'order']


@admin.register(Logement)
class LogementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'ville', 'prix', 'type_logement', 'proprietaire', 'created_at', 'photo_count']
    list_filter = ['type_logement', 'ville', 'created_at', 'climatisation', 'wifi']
    search_fields = ['titre', 'description', 'ville']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PhotoLogementInline]
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'description', 'type_logement', 'proprietaire')
        }),
        ('Localisation', {
            'fields': ('ville', 'quartier')
        }),
        ('Caractéristiques', {
            'fields': ('surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain', 'etage', 'meuble')
        }),
        ('Prix et disponibilité', {
            'fields': ('prix', 'disponible_depuis')
        }),
        ('Équipements', {
            'fields': ('climatisation', 'wifi', 'cuisine_equipee', 'garage', 'jardin', 'piscine')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'


@admin.register(PhotoLogement)
class PhotoLogementAdmin(admin.ModelAdmin):
    list_display = ['logement', 'order', 'created_at']
    list_filter = ['created_at', 'logement']
    ordering = ['logement', 'order']
