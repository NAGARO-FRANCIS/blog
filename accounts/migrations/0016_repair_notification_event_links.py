from django.db import migrations


def repair_notification_event_links(apps, schema_editor):
    notification_model = apps.get_model('accounts', 'Notification')
    table_name = notification_model._meta.db_table
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), table_name
        )
    }

    for field_name in ('related_reservation_id', 'related_payment_id'):
        if field_name not in existing_columns:
            field = notification_model._meta.get_field(field_name)
            schema_editor.add_field(notification_model, field)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0015_notification_event_links')]

    operations = [
        migrations.RunPython(
            repair_notification_event_links,
            migrations.RunPython.noop,
        ),
    ]