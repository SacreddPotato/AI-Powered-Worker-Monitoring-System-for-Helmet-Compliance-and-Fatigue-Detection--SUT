from django.db import migrations


def seed_additional_models(apps, schema_editor):
    ModelSetting = apps.get_model('detection', 'ModelSetting')
    for key in ['boots', 'faceshield', 'safetysuit']:
        ModelSetting.objects.get_or_create(key=key, defaults={'is_enabled': True})


class Migration(migrations.Migration):
    dependencies = [
        ('detection', '0002_seed_model_settings'),
    ]

    operations = [
        migrations.RunPython(seed_additional_models, migrations.RunPython.noop),
    ]
