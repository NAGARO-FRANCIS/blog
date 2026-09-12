from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logement', '0009_favorilogement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logement',
            name='type_logement',
            field=models.CharField(
                choices=[
                    ('appartement', 'Appartement'),
                    ('maison', 'Maison'),
                    ('studio', 'Studio'),
                    ('villa', 'Villa'),
                    ('chambre', 'Chambre'),
                    ('simple', 'Chambre simple'),
                    ('double', 'Chambre double'),
                    ('duplex', 'Duplex'),
                    ('suite', 'Suite'),
                    ('familiale', 'Chambre familiale'),
                ],
                default='appartement',
                max_length=20,
            ),
        ),
    ]