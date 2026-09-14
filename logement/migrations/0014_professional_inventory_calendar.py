from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('logement', '0013_logement_search_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='logement', name='unites_totales',
            field=models.PositiveIntegerField(default=1, help_text='Nombre de chambres/appartements de cette catégorie'),
        ),
        migrations.AddField(
            model_name='logement', name='politique_annulation',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='logement', name='heure_arrivee',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='logement', name='heure_depart',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='BlocageCalendrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField(help_text='Date de fin exclusive')),
                ('motif', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('logement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocages', to='logement.logement')),
            ],
            options={'ordering': ['date_debut']},
        ),
    ]