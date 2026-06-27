from django.db import migrations

def rename_colocataire_to_touriste(apps, schema_editor):
    """Renomme le rôle 'colocataire' en 'touriste' dans la base de données"""
    Profile = apps.get_model('accounts', 'Profile')
    
    # Mettre à jour tous les profils avec le rôle 'colocataire' à 'touriste'
    updated = Profile.objects.filter(role='colocataire').update(role='touriste')
    print(f"✅ {updated} profils renommés de 'colocataire' à 'touriste'")

def reverse_rename(apps, schema_editor):
    """Reverse: renomme 'touriste' en 'colocataire'"""
    Profile = apps.get_model('accounts', 'Profile')
    updated = Profile.objects.filter(role='touriste').update(role='colocataire')
    print(f"↩️ {updated} profils renommés de 'touriste' à 'colocataire'")

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_profile_options_profile_date_creation_and_more'),
    ]

    operations = [
        migrations.RunPython(rename_colocataire_to_touriste, reverse_rename),
    ]
