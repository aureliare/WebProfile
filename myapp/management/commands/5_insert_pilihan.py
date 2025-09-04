from django.core.management.base import BaseCommand
from myapp.models import Pertanyaan, Pilihan, MasterPilihan

class Command(BaseCommand):
    help = 'Insert pilihan data'

    def handle(self, *args, **kwargs):
        pertanyaan = [
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

        group_list = [
            ['Perda', 'Perbup/Perwal', 'Inbup SK Bupati', 'Peraturan/SK PD'],
            ['10 - 25%', '26 - 50%', '51 - 75%'], 
            ['Ya', 'Tidak']
        ]

        bobot = [
            [10, 5, 3, 2], 
            [2, 5, 8], 
            [8, 0]
        ]

        group_map = {
            0: (group_list[0], bobot[0]),
            1: (group_list[0], bobot[0]),
            2: (group_list[1], bobot[1]),
            3: (group_list[1], bobot[1]),
            4: (group_list[2], bobot[2]),
            5: (group_list[2], bobot[2]),
            6: (group_list[2], bobot[2]),
            7: (group_list[2], bobot[2]),
            8: (group_list[2], bobot[2]),
            9: (group_list[2], bobot[2]),
            10: (group_list[2], bobot[2]),
            11: (group_list[2], bobot[2]),
        }

        for idx, pertanyaan_text in enumerate(pertanyaan):
            # Buat atau ambil instance Pertanyaan
            pertanyaan_instance, created = Pertanyaan.objects.get_or_create(name=pertanyaan_text)

            if idx < len(group_map):
                group_items, group_bobot = group_map[idx]
                order = 0
                for item, weight in zip(group_items, group_bobot):
                    master_pilihan, created = MasterPilihan.objects.get_or_create(name=item)

                    # Buat instance Pilihan yang mengaitkan dengan pertanyaan_instance
                    pilihan_instance = Pilihan.objects.create(
                        pertanyaan=pertanyaan_instance,
                        master_pilihan=master_pilihan,
                        bobot=weight,
                        order=order
                    )
                    order += 1
                    self.stdout.write(self.style.SUCCESS(f'Data pilihan "{item}" dengan pertanyaan "{pertanyaan_text}" dengan bobot {weight} berhasil dimasukkan'))