import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates a safe, lightweight backup of the Filvora database without including temporary media downloads.'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f"Database file not found at: {db_path}"))
            return

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"filvora_backup_{timestamp}.sqlite3"
        dest_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(db_path, dest_path)
        size_kb = round(os.path.getsize(dest_path) / 1024, 2)

        self.stdout.write(self.style.SUCCESS(f"Successfully created backup: {dest_path} ({size_kb} KB)"))
