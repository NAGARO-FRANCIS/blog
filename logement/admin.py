from django.contrib import admin
from .models import Logement, PhotoLogement, VideoLogement, Reservation, Paiement, DisponibiliteCalendrier


class PhotoLogementInline(admin.TabularInline):
    model = PhotoLogement
    extra = 1
    fields = ['image', 'alt_text', 'order']


class VideoLogementInline(admin.TabularInline):
    model = VideoLogement
    extra = 1
    fields = ['video', 'titre', 'description', 'order']


@admin.register(Logement)
class LogementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'ville', 'prix', 'type_logement', 'proprietaire', 'created_at', 'photo_count', 'video_count']
    list_filter = ['type_logement', 'ville', 'created_at', 'climatisation', 'wifi']
    search_fields = ['titre', 'description', 'ville']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PhotoLogementInline, VideoLogementInline]
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

    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Vidéos'


@admin.register(PhotoLogement)
class PhotoLogementAdmin(admin.ModelAdmin):
    list_display = ['logement', 'order', 'created_at']
    list_filter = ['created_at', 'logement']
    ordering = ['logement', 'order']


@admin.register(VideoLogement)
class VideoLogementAdmin(admin.ModelAdmin):
    list_display = ['logement', 'titre', 'order', 'created_at']
    list_filter = ['created_at', 'logement']
    ordering = ['logement', 'order']
    search_fields = ['titre', 'description', 'logement__titre']


# ================================
# ADMIN POUR RÉSERVATIONS
# ================================

class PaiementInline(admin.StackedInline):
    """Afficher les paiements inline dans la réservation"""
    model = Paiement
    extra = 0
    readonly_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'created_at', 'completed_at']
    fields = ['montant', 'methode', 'statut', 'stripe_payment_intent_id', 'created_at']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin pour les réservations"""
    list_display = ['logement', 'client_display', 'date_arrivee', 'date_depart', 'nombre_nuits', 'montant_final', 'statut', 'paye']
    list_filter = ['statut', 'paye', 'date_arrivee', 'date_depart', 'created_at']
    search_fields = ['logement__titre', 'client_nom', 'client_email', 'client_telephone']
    readonly_fields = ['nombre_nuits', 'prix_total', 'montant_final', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Logement et Client', {
            'fields': ('logement', 'client_user', 'client_nom', 'client_email', 'client_telephone')
        }),
        ('Dates', {
            'fields': ('date_arrivee', 'date_depart', 'nombre_nuits')
        }),
        ('Détails réservation', {
            'fields': ('nombre_personnes', 'nombre_chambres', 'remarques')
        }),
        ('Tarification', {
            'fields': ('prix_par_nuit', 'prix_total', 'frais_service', 'frais_nettoyage_reservation', 'montant_final')
        }),
        ('Statut', {
            'fields': ('statut', 'paye')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PaiementInline]
    date_hierarchy = 'date_arrivee'
    ordering = ['-created_at']
    
    def client_display(self, obj):
        """Afficher le nom du client"""
        if obj.client_user:
            return f"{obj.client_user.get_full_name() or obj.client_user.username} (User)"
        return f"{obj.client_nom} (Touriste)"
    client_display.short_description = 'Client'


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    """Admin pour les paiements"""
    list_display = ['reservation', 'montant', 'methode', 'statut', 'created_at']
    list_filter = ['statut', 'methode', 'created_at']
    search_fields = ['reservation__logement__titre', 'reservation__client_nom']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'created_at', 'completed_at']
    
    fieldsets = (
        ('Réservation', {
            'fields': ('reservation',)
        }),
        ('Détails Paiement', {
            'fields': ('montant', 'methode', 'statut')
        }),
        ('Références Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    def get_readonly_fields(self, request, obj=None):
        """Rendre plus de champs read-only pour paiements complétés"""
        readonly = list(self.readonly_fields)
        if obj and obj.statut == 'completed':
            readonly.extend(['montant', 'methode', 'reservation'])
        return readonly


@admin.register(DisponibiliteCalendrier)
class DisponibiliteCalendrierAdmin(admin.ModelAdmin):
    """Admin pour la gestion des disponibilités"""
    list_display = ['logement', 'date', 'statut', 'prix_special']
    list_filter = ['statut', 'date', 'logement']
    search_fields = ['logement__titre']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Logement et Date', {
            'fields': ('logement', 'date')
        }),
        ('Disponibilité', {
            'fields': ('statut', 'prix_special')
        }),
    )
    
    actions = ['marquer_disponible', 'marquer_occupe', 'marquer_bloque']
    
    def marquer_disponible(self, request, queryset):
        updated = queryset.update(statut='disponible')
        self.message_user(request, f"✅ {updated} jours marqués comme disponibles")
    marquer_disponible.short_description = "✅ Marquer comme disponible"
    
    def marquer_occupe(self, request, queryset):
        updated = queryset.update(statut='occupe')
        self.message_user(request, f"❌ {updated} jours marqués comme occupés")
    marquer_occupe.short_description = "❌ Marquer comme occupé"
    
    def marquer_bloque(self, request, queryset):
        updated = queryset.update(statut='bloquer')
        self.message_user(request, f"🚫 {updated} jours marqués comme bloqués")
    marquer_bloque.short_description = "🚫 Marquer comme bloqué"
