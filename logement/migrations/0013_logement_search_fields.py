from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0012_avislogement_signalementavis'),
    ]

    operations = [
        migrations.AddField(
            model_name='logement', name='commune',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='logement', name='eau',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='logement', name='electricite',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='logement', name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='logement', name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='logement', name='distance_universite',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Distance en km', max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='logement', name='distance_hopital',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Distance en km', max_digits=7, null=True),
        ),
    ]