# insert_klaster.py

from django.core.management.base import BaseCommand
from myapp.models import Klaster
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert klaster data'

    def handle(self, *args, **kwargs):
        list = [
            'Kelembagaan','KLASTER I: HAK SIPIL DAN KEBEBASAN','KLASTER II: LINGKUNGAN DAN PENGASUHAN ALTERNATIF','KLASTER III: KESEHATAN DASAR DAN KESEJAHTERAAN',
            'KLASTER IV','KLASTER V: PERLINDUNGAN KHUSUS','KELANA','DEKELA',
        ]

        for name in list:
            # Cek jika klaster sudah ada
            if not Klaster.objects.filter(name=name).exists():
                Klaster.objects.create(name=name)
                self.stdout.write(self.style.SUCCESS(f'Data instansi "{name}" berhasil dimasukkan'))
            else:
                self.stdout.write(self.style.WARNING(f'Data instansi "{name}" sudah ada, tidak dimasukkan'))
