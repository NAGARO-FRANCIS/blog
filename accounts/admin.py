from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Profile, DocumentVerification, VerificationLog, ProfessionalProfile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'role', 'verification_status_badge', 'ville', 'date_creation']
    list_filter = ['role', 'verification_status', 'sexe', 'date_creation']
    search_fields = ['user__username', 'user__email', 'profession', 'ville', 'numero_piece_identite']
    readonly_fields = ['user', 'date_creation', 'derniere_connexion', 'verification_date']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('telephone', 'date_naissance', 'sexe', 'profession')
        }),
        ('Informations du profil', {
            'fields': ('role', 'ville', 'quartier', 'photo_profil')
        }),
        ('Pièce d\'identité', {
            'fields': ('type_piece_identite', 'numero_piece_identite')
        }),
        ('Vérification', {
            'fields': ('verification_status', 'verified', 'verification_date'),
            'description': 'Statut de vérification et conformité'
        }),
        ('Dates', {
            'fields': ('date_creation', 'derniere_connexion'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_profiles', 'reject_profiles', 'flag_profiles']
    
    def username(self, obj):
        return obj.user.username
    username.short_description = 'Utilisateur'
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nom complet'
    
    def verification_status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'verified': '#22c55e',
            'rejected': '#dc2626',
            'flagged': '#f59e0b',
        }
        color = colors.get(obj.verification_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600;">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    verification_status_badge.short_description = 'Statut'
    
    def approve_profiles(self, request, queryset):
        count = queryset.update(verification_status='verified', verified=True, verification_date=timezone.now())
        self.message_user(request, f'{count} profil(s) approuvé(s)')
    approve_profiles.short_description = "✅ Approuver les profils sélectionnés"
    
    def reject_profiles(self, request, queryset):
        count = queryset.update(verification_status='rejected', verified=False)
        self.message_user(request, f'{count} profil(s) rejeté(s)')
    reject_profiles.short_description = "❌ Rejeter les profils sélectionnés"
    
    def flag_profiles(self, request, queryset):
        count = queryset.update(verification_status='flagged')
        self.message_user(request, f'{count} profil(s) signalé(s)')
    flag_profiles.short_description = "⚠️ Signaler les profils sélectionnés"


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ['username', 'document_type', 'status_badge', 'uploaded_at', 'verified_at']
    list_filter = ['status', 'document_type', 'uploaded_at']
    search_fields = ['profile__user__username', 'profile__user__email', 'admin_notes']
    readonly_fields = ['profile', 'document_file', 'uploaded_at', 'verified_at', 'file_hash', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Document', {
            'fields': ('profile', 'document_type', 'document_file')
        }),
        ('Vérification', {
            'fields': ('status', 'admin_notes', 'rejection_reason', 'verified_by', 'verified_at')
        }),
        ('Sécurité & Audit', {
            'fields': ('file_hash', 'ip_address', 'user_agent', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_documents', 'reject_documents']
    
    def username(self, obj):
        return obj.profile.user.username
    username.short_description = 'Utilisateur'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'verified': '#22c55e',
            'rejected': '#dc2626',
            'flagged': '#f59e0b',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def approve_documents(self, request, queryset):
        count = queryset.update(status='verified', verified_by=request.user, verified_at=timezone.now())
        
        # Mettre à jour le profil si tous les documents sont approuvés
        for doc in queryset:
            if doc.is_complete_verification():
                doc.profile.verification_status = 'verified'
                doc.profile.verified = True
                doc.profile.verification_date = timezone.now()
                doc.profile.save()
        
        self.message_user(request, f'{count} document(s) approuvé(s)')
    approve_documents.short_description = "✅ Approuver les documents sélectionnés"
    
    def reject_documents(self, request, queryset):
        # Remplir les raisons de rejet si nécessaire
        for doc in queryset:
            if not doc.rejection_reason:
                doc.rejection_reason = "Document non conforme"
                doc.save()
        count = queryset.update(status='rejected', verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f'{count} document(s) rejeté(s)')
    reject_documents.short_description = "❌ Rejeter les documents sélectionnés"


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['profile__user__username', 'details', 'ip_address']
    readonly_fields = ['profile', 'action', 'details', 'performed_by', 'ip_address', 'timestamp']
    
    fieldsets = (
        ('Audit', {
            'fields': ('profile', 'action', 'details', 'performed_by', 'timestamp', 'ip_address')
        }),
    )
    
    def username(self, obj):
        return obj.profile.user.username
    username.short_description = 'Utilisateur'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ['establishment_name', 'get_establishment_type_display', 'legal_representative', 'number_of_rooms', 'is_verified_badge', 'created_at']
    list_filter = ['establishment_type', 'is_verified', 'created_at']
    search_fields = ['establishment_name', 'siret_or_rccm', 'legal_representative', 'profile__user__username']
    readonly_fields = ['profile', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Établissement', {
            'fields': ('profile', 'establishment_type', 'establishment_name', 'siret_or_rccm')
        }),
        ('Représentant légal', {
            'fields': ('legal_representative', 'legal_phone')
        }),
        ('Localisation', {
            'fields': ('establishment_address', 'establishment_city', 'establishment_postal_code', 'establishment_country')
        }),
        ('Détails', {
            'fields': ('number_of_rooms', 'number_of_floors', 'website')
        }),
        ('Équipements', {
            'fields': ('wifi', 'parking', 'restaurant', 'reception_24h', 'air_conditioning', 'laundry_service', 'gym', 'conference_room'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('legal_document', 'establishment_photo')
        }),
        ('Vérification', {
            'fields': ('is_verified', 'verification_date')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_establishments', 'unverify_establishments']
    
    def is_verified_badge(self, obj):
        color = '#22c55e' if obj.is_verified else '#f59e0b'
        status = '✅ Vérifié' if obj.is_verified else '⏳ En attente'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600;">{}</span>',
            color,
            status
        )
    is_verified_badge.short_description = 'Statut'
    
    def verify_establishments(self, request, queryset):
        count = queryset.update(is_verified=True, verification_date=timezone.now())
        self.message_user(request, f'{count} établissement(s) vérifié(s)')
    verify_establishments.short_description = "✅ Vérifier les établissements sélectionnés"
    
    def unverify_establishments(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f'{count} établissement(s) non vérifié(s)')
    unverify_establishments.short_description = "❌ Retirer la vérification"
