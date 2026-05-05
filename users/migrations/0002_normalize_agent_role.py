from django.db import migrations, models


def normalize_agent_role(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(role='agnet').update(role='agent')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_agent_role, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrateur'),
                    ('directeur', 'Directeur'),
                    ('agent', 'Agent'),
                ],
                max_length=20,
            ),
        ),
    ]
