# insert_pertanyaan.py

from django.core.management.base import BaseCommand
from myapp.models import Pertanyaan
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert pertanyaan data'

    def handle(self, *args, **kwargs):
        list = [
            'Apakah tersedia peraturan daerah terkait Pemenuhan Hak Anak pada Perangkat Daerah dalam mewujudkan Kabupaten/Kota Layak Anak? (Lampirkan Dokumen Pendukung)',
            'Apakah tersedia peraturan/ kebijakan terkait Partisipasi Anak pada Perangkat Daerah atau lembaga lainnya',
            'Apakah ada anggaran dari Perangkat Daerah dan anggaran lainnya untuk mendukung terhadap pemenuhan hak anak dan perlindungan anak (lampirkan data dukung APBD anggaran lainnya yang ditandatangani Kepala Perangkat Daerah + Stempel Basah)',
            'apakah ada anggaran dari Pemerintah Daerah dan anggaran lainnya untuk terlembaga-nya partisipasi anak (lampirkan data dukung APBD anggaran lainnya yang ditandatangani Kepala Perangkat Daerah + Stempel Basah)',
            'Apakah dalam proses penyusunan peraturan terkait dengan KLA di daerah telah mendengarkan dan mempertimbangkan pandangan/pendapat/usulan dari kelompok anak? (Lampirkan dokumen usulan dokumen akhir/tindak lanjut/kebijakan atau foto dan berita yang dimuat (di-upload) di media sosial)',
            'Apakah ada Komunikasi, Informasi, dan Edukasi (KIE) dan Publikasi KLA yang dikembangkan oleh Perangkat Daerah dalam satu tahun terakhir ? (LAMPIRKAN FOTO PENDUKUNG)',
            'Apakah kelompok anak sudah dilibatkan dalam proses penyusunan perencanaan program/kegiatan pada Perangkat Daerah? (Lampirkan MATRIKS dan dokumen pendukung)',
            'RUANG BERMAIN RUMAH ANAK (RBRA) apakah ada Ruang Bermain Anak (RBA) pada Perangkat Daerah ? (lampirkan dokumen pendukung)',
            'Apakah Perangkat Daerah memiliki Ruang ASI/LAKTASI? (Lampirkan dokumen pendukung berupa data ruang ASI di kantor, jumlah perkantoran yang ada dan dokumentasi) Jelaskan upaya yang telah dilakukan untuk meningkatkan cakupan ruang ASI di perkantoran!',
            'Apakah sarana dan prasarana pada Perangkat Daerah telah memperlihatkan aksesibilitas bagi anak penyandang disabilitas? (Lampirkan dokumen pendukung)',
            'Apakah ada Inovasi terkait Pemenuhan Hak Anak dan Perlindungan Khusus Anak pada Setiap Perangkat Daerah ?',
            'Apakah ada kemitraan antar Perangkat Daerah dan/atau masyarakat dalam pemenuhan Hak Anak dan Perlindungan Khusus Anak ? Jelaskan peran masing-masing dalam matriks. (Lampirkan matriks dan dokumen pendukung)'
        ]

        type = 'multiple'
        category = 'baku'

        description = 'Penjelasan'
        evaluation_note = 'Penjelasan'

        for name in list:
            # Cek jika kombinasi text dan bobot sudah ada
            if not Pertanyaan.objects.filter(name=name, type=type, category=category, description=description).exists():
                Pertanyaan.objects.create(name=name, type=type, category=category, description=description,evaluation_note=evaluation_note)
                self.stdout.write(self.style.SUCCESS(f'Data pertanyaan "{name}" dengan jenis {type} dengan kategori {category} dengan penjelasan {description} berhasil dimasukkan'))
            else:
                self.stdout.write(self.style.WARNING(f'Data pertanyaan "{name}" dengan jenis {type} dengan kategori {category} dengan penjelasan {description} sudah ada, tidak dimasukkan'))
