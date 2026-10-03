from django.db import migrations, models
import django.db.models.deletion


def create_units_and_assign_existing_reservations(apps, schema_editor):
    Logement = apps.get_model('logement', 'Logement')
    UniteLogement = apps.get_model('logement', 'UniteLogement')
    Reservation = apps.get_model('logement', 'Reservation')
    database = schema_editor.connection.alias

    for logement in Logement.objects.using(database).filter(
        account_type__in=['hotel', 'residence'],
    ).iterator():
        units = [
            UniteLogement(logement_id=logement.pk, numero=str(number))
            for number in range(1, logement.unites_totales + 1)
        ]
        UniteLogement.objects.using(database).bulk_create(units)
        units = list(
            UniteLogement.objects.using(database)
            .filter(logement_id=logement.pk)
            .order_by('id')
        )
        assigned = {unit.pk: [] for unit in units}
        unassigned_stays = []
        reservations = Reservation.objects.using(database).filter(
            logement_id=logement.pk,
            statut__in=['pending', 'confirmed'],
        ).order_by('date_arrivee', 'created_at', 'pk')

        for reservation in reservations.iterator():
            available = [
                unit_id for unit_id, stays in assigned.items()
                if all(
                    reservation.date_arrivee >= departure
                    or reservation.date_depart <= arrival
                    for arrival, departure in stays
                )
                and all(
                    reservation.date_arrivee >= departure
                    or reservation.date_depart <= arrival
                    for arrival, departure in unassigned_stays
                )
            ]
            room_count = reservation.nombre_chambres or 1
            if len(available) < room_count:
                unassigned_stays.append((reservation.date_arrivee, reservation.date_depart))
                continue
            allocated = available[:room_count]
            through = Reservation.unites.through
            through.objects.using(database).bulk_create([
                through(reservation_id=reservation.pk, unitelogement_id=unit_id)
                for unit_id in allocated
            ])
            for unit_id in allocated:
                assigned[unit_id].append((reservation.date_arrivee, reservation.date_depart))


class Migration(migrations.Migration):
    dependencies = [
        ('logement', '0016_paiement_cinetpay_payment_token_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UniteLogement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=30)),
                ('logement', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unites',
                    to='logement.logement',
                )),
            ],
            options={
                'ordering': ['numero'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('logement', 'numero'),
                        name='unique_numero_unite_par_logement',
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name='reservation',
            name='unites',
            field=models.ManyToManyField(
                blank=True,
                related_name='reservations',
                to='logement.unitelogement',
            ),
        ),
        migrations.RunPython(
            create_units_and_assign_existing_reservations,
            migrations.RunPython.noop,
        ),
    ]
