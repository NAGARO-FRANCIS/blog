from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0019_paiement_cinetpay_notify_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='statut',
            field=models.CharField(
                choices=[
                    ('pending', '⏳ En attente de paiement'),
                    ('confirmed', '✅ Confirmée'),
                    ('checked_in', '🏨 En séjour'),
                    ('cancelled', '❌ Annulée'),
                    ('completed', '✓ Complétée'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
