# insert_instansi.py

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import User, Instansi
import sys
import os
from django.core.exceptions import ObjectDoesNotExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = 'Insert instansi data'

    def handle(self, *args, **kwargs):
        list = [
            'Superuser','Admin','Verifikator','User',
            'Asisten Administrasi Umum','Asisten Ekonomi dan Pembangunan','Asisten Pemerintahan dan Kesejahteraan Rakyat','Badan Kepegawaian & Pengembangan Sumber Daya Manusia','Badan Kesatuan Bangsa dan Politik','Badan Penanggulangan Bencana Daerah (bpbd)','Badan Pendapatan Daerah','Badan Penelitian dan Pengembangan Daerah','Badan Pengelolaan Keuangan Daerah','Badan Perencanaan Pembangunan Daerah','Bagian Administrasi Kesejahteraan Rakyat','Bagian Administrasi Pembangunan','Bagian Administrasi Pemerintahan','Bagian Administrasi Perekonomian','Bagian Hukum','Bagian Kerjasama','Bagian Layanan Pengadaan Barang dan Jasa','Bagian Organisasi','Bagian Perencanaan dan Keuangan Sekretariat Daerah Kabupaten Bekasi','Bagian Perlengkapan','Bagian Protokol dan Komunikasi Pimpinan','Bagian Umum','Dinas Arsip dan Perpustakaan','Dinas Cipta Karya dan Tata Ruang','Dinas Kebudayaan, Pemuda dan Olahraga','Dinas Kependudukan dan Pencatatan Sipil','Dinas Kesehatan','Dinas Ketahanan Pangan','Dinas Komunikasi, Informatika Persandian dan Statistik','Dinas Koperasi dan UMKM','Dinas Lingkungan Hidup','Dinas Pariwisata','Dinas Pemadam Kebakaran','Dinas Pemberdayaan Masyarakat dan Desa','Dinas Pemberdayaan Perempuan dan Perlindungan Anak','Dinas Penanaman Modal dan Pelayanan Perizinan Terpadu Satu Pintu','Dinas Pendidikan','Dinas Pengendalian Penduduk dan Keluarga Berencana','Dinas Perdagangan','Dinas Perhubungan','Dinas Perikanan dan Kelautan','Dinas Perindustrian','Dinas Pertanian','Dinas Perumahan Rakyat, Kawasan Permukiman dan Pertanahan','Dinas Sosial','Dinas Sumber Daya Air,Bina Marga dan Bina Kontruksi','Dinas Tenaga Kerja','Inspektorat','Kecamatan Babelan','Kecamatan Bojongmangu','Kecamatan Cabangbungin','Kecamatan Cibarusah','Kecamatan Cibitung','Kecamatan Cikarang Barat','Kecamatan Cikarang Pusat','Kecamatan Cikarang Selatan','Kecamatan Cikarang Timur','Kecamatan Cikarang Utara','Kecamatan Karangbahagia','Kecamatan Kedungwaringin','Kecamatan Muara Gembong','Kecamatan Pebayuran','Kecamatan Serang Baru','Kecamatan Setu','Kecamatan Sukakarya','Kecamatan Sukatani','Kecamatan Sukawangi','Kecamatan Tambelang','Kecamatan Tambun Selatan','Kecamatan Tambun Utara','Kecamatan Tarumajaya','PDAM','PLN','Puskesmas Waluya CIKUT','Rumah Sakit Umum Daerah (rsud)','Satuan Polisi Pamong Praja (satpolpp)','Sekretariat DPRD'
        ]

        # Menentukan role berdasarkan nama
        role_mapping = {
            'admin': 'admin',
            'verifikator': 'verifikator'
        }

        for name in list:
            # Cek jika instansi sudah ada
            if not User.objects.filter(first_name=name).exists():
                try:
                    # Retrieve the instansi by name
                    instansi_instance = Instansi.objects.get(name=name)
                except ObjectDoesNotExist:
                    try:
                        # If not found, get the default instansi
                        instansi_instance = Instansi.objects.get(name='Dinas Pemberdayaan Perempuan dan Perlindungan Anak')
                    except ObjectDoesNotExist:
                        # Handle the case where the default instansi also does not exist
                        instansi_instance = None  # or handle as needed

                # Check if instansi_instance is valid before accessing its ID
                if instansi_instance is not None:
                    instansi_id = instansi_instance.id
                    # Use instansi_id as needed
                else:
                    self.stdout.write(self.style.ERROR('No valid instansi found.'))

                
                if name.lower() == 'superuser':
                    user = User.objects.create(
                        first_name=name,
                        username='superuser',  # Username tetap superuser
                        email='superuser@bekasikab.go.id',  # Email tetap untuk superuser
                        password=make_password('password12345'),
                        is_active=True,
                        is_superuser=True,  # Set is_superuser ke True
                        is_staff=True,
                        role='admin',
                        instansi_id=instansi_id,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Data pengguna "{name}" berhasil dimasukkan sebagai superuser'))
                else:
                    # Menghasilkan username dan email yang unik
                    base_username = 'username'
                    base_email = "email@example.com"
                    
                    # Increment username dan email jika sudah ada
                    count = 1
                    while User.objects.filter(username=base_username).exists() or User.objects.filter(email=base_email).exists():
                        base_username = f"username{count}"
                        base_email = f"email{count}@bekasikab.go.id"
                        count += 1
                    
                    role = role_mapping.get(name.lower(), 'operator')

                    user = User.objects.create(
                        first_name=name,
                        username=base_username,
                        email=base_email,
                        password=make_password('bekasikab24'),
                        is_active=False,
                        role=role,
                        instansi_id=instansi_id
                    )
                    self.stdout.write(self.style.SUCCESS(f'Data pengguna "{name}" berhasil dimasukkan'))

            else:
                self.stdout.write(self.style.WARNING(f'Data pengguna "{name}" sudah ada, tidak dimasukkan'))
