from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0021_residence_daily_rental_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiement',
            name='statut',
            field=models.CharField(
                choices=[
                    ('pending', '⏳ En attente'),
                    ('completed', '✅ Complété'),
                    ('failed', '❌ Échoué'),
                    ('refunded', '↩️ Remboursé'),
                    ('cancelled', '❌ Annulé'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
