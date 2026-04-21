from django.core.management.base import BaseCommand
from detection.models import ModelSetting
from config import MODEL_DEFINITIONS

class Command(BaseCommand):
    help = 'Ensures all models from config.py are registered in the database'

    def handle(self, *args, **options):
        self.stdout.write('Checking model settings...')
        for key, defn in MODEL_DEFINITIONS.items():
            obj, created = ModelSetting.objects.get_or_create(
                key=key,
                defaults={'is_enabled': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created model: {key}'))
            else:
                self.stdout.write(f'Model exists: {key}')
        
        # Disable models not in config if any
        existing_keys = set(MODEL_DEFINITIONS.keys())
        ModelSetting.objects.exclude(key__in=existing_keys).update(is_enabled=False)
        self.stdout.write(self.style.SUCCESS('Model seeding complete.'))
