from django.db import migrations, models
import django.db.models.deletion


def attach_existing_professional_listings(apps, schema_editor):
    Etablissement = apps.get_model('logement', 'Etablissement')
    Logement = apps.get_model('logement', 'Logement')

    owner_ids = Logement.objects.filter(
        account_type__in=['hotel', 'residence'],
        proprietaire__isnull=False,
    ).values_list('proprietaire_id', flat=True).distinct()

    for owner_id in owner_ids:
        listings = Logement.objects.filter(
            proprietaire_id=owner_id,
            account_type__in=['hotel', 'residence'],
        ).order_by('created_at')
        first_listing = listings.first()
        if not first_listing:
            continue

        owner = first_listing.proprietaire
        full_name = f"{owner.first_name} {owner.last_name}".strip()
        establishment, _ = Etablissement.objects.get_or_create(
            proprietaire_id=owner_id,
            defaults={
                'nom': full_name or owner.username,
                'type_etablissement': first_listing.account_type,
                'ville': first_listing.ville,
                'quartier': first_listing.quartier,
            },
        )
        listings.update(etablissement_id=establishment.id)


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0010_alter_logement_type_logement'),
    ]

    operations = [
        migrations.CreateModel(
            name='Etablissement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('type_etablissement', models.CharField(choices=[('hotel', 'Hotel'), ('residence', 'Residence')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('ville', models.CharField(max_length=100)),
                ('quartier', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proprietaire', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='etablissement_logement', to='auth.user')),
            ],
            options={
                'verbose_name': 'Etablissement',
                'verbose_name_plural': 'Etablissements',
                'ordering': ['nom'],
            },
        ),
        migrations.AddField(
            model_name='logement',
            name='etablissement',
            field=models.ForeignKey(blank=True, help_text='Etablissement auquel cette chambre ou ce logement appartient', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', to='logement.etablissement'),
        ),
        migrations.RunPython(attach_existing_professional_listings, migrations.RunPython.noop),
    ]