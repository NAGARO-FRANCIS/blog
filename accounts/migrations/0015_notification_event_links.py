from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0014_profileverification')]

    operations = [
        migrations.AddField(
            model_name='notification', name='related_reservation_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification', name='related_payment_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notification', name='notification_type',
            field=models.CharField(choices=[
                ('new_listing', 'Nouvelle annonce'), ('subscription', 'Nouvel abonné'),
                ('message', 'Nouveau message'), ('reservation', 'Nouvelle réservation'),
                ('payment', 'Paiement reçu'), ('favorite', 'Ajout aux favoris'),
                ('approval', 'Annonce approuvée'), ('system', 'Notification système'),
            ], default='system', max_length=20),
        ),
    ]