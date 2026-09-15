from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('messagerie', '0005_appelsession_appelsignal'),
    ]

    operations = [
        migrations.AddField(
            model_name='appelsession',
            name='media_type',
            field=models.CharField(default='video', max_length=5),
        ),
    ]