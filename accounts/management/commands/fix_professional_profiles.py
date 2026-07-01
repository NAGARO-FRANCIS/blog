from django.core.management.base import BaseCommand, CommandError
from accounts.models import ProfessionalProfile, Profile


class Command(BaseCommand):
    help = 'Trouve les ProfessionalProfile par nom d\'établissement et met à jour le Profile associé (account_type=hotel, role=proprietaire)'

    def add_arguments(self, parser):
        parser.add_argument('--query', '-q', type=str, required=True, help='Sous-chaîne du nom d\'établissement à rechercher')
        parser.add_argument('--apply', action='store_true', help='Appliquer les changements (par défaut dry-run)')

    def handle(self, *args, **options):
        query = options['query']
        do_apply = options['apply']

        matches = ProfessionalProfile.objects.filter(establishment_name__icontains=query)
        if not matches.exists():
            self.stdout.write(self.style.WARNING(f"Aucun ProfessionalProfile trouvé pour: '{query}'"))
            return

        for prof in matches:
            profile = prof.profile
            self.stdout.write(f"Trouvé: établissement='{prof.establishment_name}', utilisateur='{profile.user.username}' (profile id={profile.id})")
            self.stdout.write(f"  Avant: account_type={profile.account_type}, role={profile.role}")
            if do_apply:
                profile.account_type = 'hotel'
                profile.role = 'proprietaire'
                profile.save()
                self.stdout.write(self.style.SUCCESS(f"  Mis à jour: account_type=hotel, role=proprietaire pour user={profile.user.username}"))
            else:
                self.stdout.write(self.style.NOTICE("  Dry-run: pas de modification. Rerun with --apply to update."))
