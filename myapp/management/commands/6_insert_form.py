# insert_form.py

from django.core.management.base import BaseCommand
from myapp.models import Form
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert instansi data'

    def handle(self, *args, **kwargs):
        list = [
            'EVALUASI KABUPATEN LAYAK ANAK TAHUN 2024'
        ]

        for name in list:
            # Cek jika instansi sudah ada
            if not Form.objects.filter(name=name,year=2024).exists():
                Form.objects.create(name=name,year=2024,start='2024-10-10 06:00:00',end='2024-12-30 10:00:00')
                self.stdout.write(self.style.SUCCESS(f'Data form "{name}" berhasil dimasukkan'))
            else:
                self.stdout.write(self.style.WARNING(f'Data form "{name}" sudah ada, tidak dimasukkan'))
