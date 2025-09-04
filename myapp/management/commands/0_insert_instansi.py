# insert_instansi.py

from django.core.management.base import BaseCommand
from myapp.models import Instansi
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert instansi data'

    def handle(self, *args, **kwargs):
        list = [
            'Asisten Administrasi Umum','Asisten Ekonomi dan Pembangunan','Asisten Pemerintahan dan Kesejahteraan Rakyat','Badan Kepegawaian & Pengembangan Sumber Daya Manusia','Badan Kesatuan Bangsa dan Politik','Badan Penanggulangan Bencana Daerah (bpbd)','Badan Pendapatan Daerah','Badan Penelitian dan Pengembangan Daerah','Badan Pengelolaan Keuangan Daerah','Badan Perencanaan Pembangunan Daerah','Bagian Administrasi Kesejahteraan Rakyat','Bagian Administrasi Pembangunan','Bagian Administrasi Pemerintahan','Bagian Administrasi Perekonomian','Bagian Hukum','Bagian Kerjasama','Bagian Layanan Pengadaan Barang dan Jasa','Bagian Organisasi','Bagian Perencanaan dan Keuangan Sekretariat Daerah Kabupaten Bekasi','Bagian Perlengkapan','Bagian Protokol dan Komunikasi Pimpinan','Bagian Umum','Dinas Arsip dan Perpustakaan','Dinas Cipta Karya dan Tata Ruang','Dinas Kebudayaan, Pemuda dan Olahraga','Dinas Kependudukan dan Pencatatan Sipil','Dinas Kesehatan','Dinas Ketahanan Pangan','Dinas Komunikasi, Informatika Persandian dan Statistik','Dinas Koperasi dan UMKM','Dinas Lingkungan Hidup','Dinas Pariwisata','Dinas Pemadam Kebakaran','Dinas Pemberdayaan Masyarakat dan Desa','Dinas Pemberdayaan Perempuan dan Perlindungan Anak','Dinas Penanaman Modal dan Pelayanan Perizinan Terpadu Satu Pintu','Dinas Pendidikan','Dinas Pengendalian Penduduk dan Keluarga Berencana','Dinas Perdagangan','Dinas Perhubungan','Dinas Perikanan dan Kelautan','Dinas Perindustrian','Dinas Pertanian','Dinas Perumahan Rakyat, Kawasan Permukiman dan Pertanahan','Dinas Sosial','Dinas Sumber Daya Air,Bina Marga dan Bina Kontruksi','Dinas Tenaga Kerja','Inspektorat','Kecamatan Babelan','Kecamatan Bojongmangu','Kecamatan Cabangbungin','Kecamatan Cibarusah','Kecamatan Cibitung','Kecamatan Cikarang Barat','Kecamatan Cikarang Pusat','Kecamatan Cikarang Selatan','Kecamatan Cikarang Timur','Kecamatan Cikarang Utara','Kecamatan Karangbahagia','Kecamatan Kedungwaringin','Kecamatan Muara Gembong','Kecamatan Pebayuran','Kecamatan Serang Baru','Kecamatan Setu','Kecamatan Sukakarya','Kecamatan Sukatani','Kecamatan Sukawangi','Kecamatan Tambelang','Kecamatan Tambun Selatan','Kecamatan Tambun Utara','Kecamatan Tarumajaya','PDAM','PLN','Puskesmas Waluya CIKUT','Rumah Sakit Umum Daerah (rsud)','Satuan Polisi Pamong Praja (satpolpp)','Sekretariat DPRD'
        ]

        for name in list:
            # Cek jika instansi sudah ada
            if not Instansi.objects.filter(name=name).exists():
                Instansi.objects.create(name=name)
                self.stdout.write(self.style.SUCCESS(f'Data instansi "{name}" berhasil dimasukkan'))
            else:
                self.stdout.write(self.style.WARNING(f'Data instansi "{name}" sudah ada, tidak dimasukkan'))
