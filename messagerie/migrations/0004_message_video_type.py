from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('messagerie', '0003_alter_message_message_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_type',
            field=models.CharField(
                choices=[
                    ('text', 'Texte'),
                    ('image', 'Image'),
                    ('file', 'Fichier'),
                    ('audio', 'Audio'),
                    ('video', 'Vidéo'),
                    ('system', 'Système'),
                ],
                default='text',
                max_length=10,
            ),
        ),
    ]
