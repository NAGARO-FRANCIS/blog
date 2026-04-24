from django.contrib import admin
from .models import ColocationAnnonce, PhotoColocation, Favori


class PhotoColocationInline(admin.TabularInline):
    model = PhotoColocation
    extra = 1
    fields = ['image', 'alt_text', 'order']


@admin.register(ColocationAnnonce)
class ColocationAnnonceAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'nombre_colocataires', 'proprietaire', 'created_at', 'photo_count']
    list_filter = ['ville', 'profil_recherche', 'meuble', 'created_at', 'climatisation', 'wifi']
    search_fields = ['description', 'infos_logement', 'ville', 'proprietaire__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PhotoColocationInline]
    fieldsets = (
        ('Annonce', {
            'fields': ('proprietaire', 'description')
        }),
        ('Localisation', {
            'fields': ('ville', 'quartier')
        }),
        ('Budget et logement', {
            'fields': ('budget_mensuel', 'surface', 'nombre_chambres', 'nombre_salles_bain')
        }),
        ('Colocataires', {
            'fields': ('nombre_colocataires', 'profil_recherche', 'durée_minimum', 'conditions_vie')
        }),
        ('Équipements et conditions', {
            'fields': ('climatisation', 'wifi', 'cuisine_equipee', 'garage', 'jardin', 'meuble', 'disponible_depuis')
        }),
        ('Informations supplémentaires', {
            'fields': ('infos_logement',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'


@admin.register(PhotoColocation)
class PhotoColocationAdmin(admin.ModelAdmin):
    list_display = ['annonce', 'order', 'created_at']
    list_filter = ['created_at', 'annonce']
    ordering = ['annonce', 'order']


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'annonce', 'created_at']
    list_filter = ['created_at', 'utilisateur']
    search_fields = ['utilisateur__username', 'annonce__description']
