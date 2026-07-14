from django.core.management.base import BaseCommand
from accounts.models import Profile, ProfessionalProfile


class Command(BaseCommand):
    help = 'Corrige les profils de résidence/hôtel mal classés pour qu’ils publient via le bon formulaire.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Appliquer les changements')

    def handle(self, *args, **options):
        do_apply = options['apply']
        updated = []

        for profile in Profile.objects.select_related('professional_profile').all():
            professional = getattr(profile, 'professional_profile', None)
            if not professional:
                continue

            current_type = profile.account_type
            target_type = professional.establishment_type or current_type
            if current_type != target_type or profile.role != 'proprietaire':
                updated.append((profile.user.username, current_type, target_type, profile.role))
                if do_apply:
                    profile.account_type = target_type
                    profile.role = 'proprietaire'
                    profile.profession = f"Gestionnaire de {target_type}"
                    profile.save(update_fields=['account_type', 'role', 'profession'])

        if not updated:
            self.stdout.write(self.style.SUCCESS('Aucun profil à corriger.'))
            return

        self.stdout.write(self.style.WARNING(f'{len(updated)} profil(s) à corriger :'))
        for item in updated:
            self.stdout.write(f"- {item[0]}: account_type={item[1]} -> {item[2]}, role={item[3]} -> proprietaire")

        if do_apply:
            self.stdout.write(self.style.SUCCESS('Correction appliquée.'))
