from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = 'Corriger et gérer les rôles des utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            help='Action à effectuer: list, set-role, fix-users'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username de l\'utilisateur'
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Rôle à attribuer (proprietaire, locataire, colocataire)'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'list':
            self.list_users()
        elif action == 'set-role':
            self.set_role(options.get('username'), options.get('role'))
        elif action == 'fix-users':
            self.fix_users()
        else:
            self.stdout.write(self.style.ERROR(f'Action inconnue: {action}'))

    def list_users(self):
        """Lister tous les utilisateurs avec leurs rôles"""
        users = User.objects.all()
        self.stdout.write(self.style.SUCCESS('=== UTILISATEURS EXISTANTS ===\n'))
        
        for user in users:
            try:
                profile = user.profile
                self.stdout.write(
                    f'[USER] {user.username:15} | Role: {profile.role:15} | '
                    f'Type: {profile.account_type:10} | {user.get_full_name()}'
                )
            except Profile.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'[NO-PROFILE] {user.username} - Pas de profil!'))

    def set_role(self, username, role):
        """Définir le rôle d'un utilisateur"""
        if not username or not role:
            self.stdout.write(self.style.ERROR('Usage: set-role --username USERNAME --role ROLE'))
            return

        valid_roles = dict(Profile.ROLE_CHOICES).keys()
        if role not in valid_roles:
            self.stdout.write(self.style.ERROR(f'Rôle invalide. Options: {", ".join(valid_roles)}'))
            return

        try:
            user = User.objects.get(username=username)
            profile = user.profile
            old_role = profile.role
            profile.role = role
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'[SUCCESS] Role de {username} change: {old_role} -> {role}'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Utilisateur {username} introuvable'))
        except Profile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Profil pour {username} introuvable'))

    def fix_users(self):
        """Corriger automatiquement les rôles des trois utilisateurs de test"""
        fixes = [
            ('Ban', 'proprietaire', '[OWNER] Proprietaire'),
            ('Christelle', 'locataire', '[TENANT] Locataire'),
            ('Elisee', 'colocataire', '[ROOMMATE] Colocataire'),
        ]

        self.stdout.write(self.style.SUCCESS('=== CORRECTION DES ROLES ===\n'))

        for username, role, description in fixes:
            try:
                user = User.objects.get(username=username)
                profile = user.profile
                old_role = profile.role
                
                if old_role != role:
                    profile.role = role
                    profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] {description:30} {username:15} | {old_role:15} -> {role}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[SKIP] {description:30} {username:15} | Role deja correct'
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] {description:30} Utilisateur {username} introuvable')
                )
            except Profile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] {description:30} Profil pour {username} introuvable')
                )
