from django.db import migrations, models
import django.core.validators

def rename_colocataires_field(apps, schema_editor):
    """Renomme le champ nombre_colocataires en nombre_touristes"""
    ColocationAnnonce = apps.get_model('colocation', 'ColocationAnnonce')
    # Migration des données déjà gérée par Django
    print("✅ Migration du champ nombre_colocataires en nombre_touristes effectuée")

class Migration(migrations.Migration):

    dependencies = [
        ('colocation', '0003_alter_colocationannonce_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='colocationannonce',
            old_name='nombre_colocataires',
            new_name='nombre_touristes',
        ),
    ]
