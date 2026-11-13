import re

from django.db import migrations, models


def convert_legacy_lease_durations(apps, schema_editor):
    Logement = apps.get_model('logement', 'Logement')
    database = schema_editor.connection.alias

    for logement_id, value in Logement.objects.using(database).values_list(
        'pk', 'duree_min_bail'
    ).iterator():
        if value is None or not str(value).strip():
            continue

        normalized = str(value).lower()
        parts = re.findall(
            r'(\d+)\s*(ans?|années?|mois|jours?|years?|months?|days?)',
            normalized,
        )
        if parts:
            days = 0
            for amount, unit in parts:
                amount = int(amount)
                if unit.startswith(('an', 'année', 'year')):
                    days += amount * 365
                elif unit.startswith(('mois', 'month')):
                    days += amount * 30
                else:
                    days += amount
        elif normalized.strip().isdigit():
            days = int(normalized.strip()) * 30
        else:
            days = None

        Logement.objects.using(database).filter(pk=logement_id).update(
            duree_min_bail=days if days and days > 0 else None
        )


def restore_legacy_lease_durations(apps, schema_editor):
    Logement = apps.get_model('logement', 'Logement')
    database = schema_editor.connection.alias
    for logement in Logement.objects.using(database).only('pk', 'duree_min_bail').iterator():
        if logement.duree_min_bail is not None:
            Logement.objects.using(database).filter(pk=logement.pk).update(
                duree_min_bail=f'{logement.duree_min_bail} jours'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0020_reservation_checked_in_status'),
    ]

    operations = [
        migrations.RunPython(
            convert_legacy_lease_durations,
            restore_legacy_lease_durations,
        ),
        migrations.AlterField(
            model_name='logement',
            name='duree_min_bail',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]