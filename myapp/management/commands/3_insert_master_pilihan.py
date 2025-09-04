# insert_master_pilihan.py

from django.core.management.base import BaseCommand
from myapp.models import MasterPilihan
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert master pilihan data'

    def handle(self, *args, **kwargs):
        list = [
            'Perda', 'Perbup/Perwal', 'Inbup SK Bupati', 
            'Peraturan/SK PD', '10 - 25%', '26 - 50%', 
            '51 - 75%', 'Ya', 'Tidak'
        ]

        bobot = [10, 5, 3, 2, 2, 5, 8, 8, 0]

        for name, weight in zip(list, bobot):
            # Cek jika kombinasi text dan bobot sudah ada
            if not MasterPilihan.objects.filter(name=name, bobot=weight).exists():
                MasterPilihan.objects.create(name=name, bobot=weight)
                self.stdout.write(self.style.SUCCESS(f'Data pilihan "{name}" dengan bobot {weight} berhasil dimasukkan'))
            else:
                self.stdout.write(self.style.WARNING(f'Data pilihan "{name}" dengan bobot {weight} sudah ada, tidak dimasukkan'))
