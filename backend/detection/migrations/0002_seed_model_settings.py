from django.db import migrations

def seed_models(apps, schema_editor):
    ModelSetting = apps.get_model('detection', 'ModelSetting')
    for key in ['helmet', 'fatigue', 'vest', 'gloves', 'goggles']:
        ModelSetting.objects.get_or_create(key=key, defaults={'is_enabled': True})

class Migration(migrations.Migration):
    dependencies = [
        ('detection', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(seed_models, migrations.RunPython.noop),
    ]
