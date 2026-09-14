from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0011_etablissement_logement_etablissement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AvisLogement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_logement', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('note_proprietaire', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('commentaire', models.TextField()),
                ('est_visible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avis_logements', to=settings.AUTH_USER_MODEL)),
                ('logement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avis', to='logement.logement')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reponses', to='logement.avislogement')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avis', to='logement.reservation')),
            ],
            options={
                'verbose_name': 'Avis logement',
                'verbose_name_plural': 'Avis logements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SignalementAvis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motif', models.CharField(max_length=500)),
                ('traite', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signalements_avis', to=settings.AUTH_USER_MODEL)),
                ('avis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signalements', to='logement.avislogement')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='avislogement',
            constraint=models.UniqueConstraint(fields=('reservation', 'auteur'), name='unique_avis_par_reservation'),
        ),
        migrations.AddConstraint(
            model_name='signalementavis',
            constraint=models.UniqueConstraint(fields=('avis', 'auteur'), name='unique_signalement_avis_par_utilisateur'),
        ),
    ]