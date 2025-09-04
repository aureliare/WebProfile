from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import os

class Instansi(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Instansi"
        verbose_name_plural = "Instansi"

    def __str__(self):
        return self.name

class User(AbstractUser):
    ADMIN = 'admin'
    USER = 'user'
    VERIFIKATOR = 'verifikator'
    OPERATOR = 'operator'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (USER, 'User'),
        (VERIFIKATOR, 'Verifikator'),
        (OPERATOR, 'Operator'),
    ]

    instansi = models.ForeignKey(Instansi, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Pengguna"

    def __str__(self):
        return self.username

class Klaster(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Klaster"
        verbose_name_plural = "Klaster"

    def __str__(self):
        return self.name

class Indikator(models.Model):
    name = models.CharField(max_length=255)
    klaster = models.ForeignKey(Klaster, on_delete=models.CASCADE, null=True, blank=True, related_name='indikators')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Indikator"
        verbose_name_plural = "Indikator"

    def __str__(self):
        return self.name

class Form(models.Model):
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    start = models.DateTimeField(null=True, blank=True)  # Menggunakan DateTimeField untuk menyimpan tanggal dan waktu
    end = models.DateTimeField(null=True, blank=True)    # Menggunakan DateTimeField untuk menyimpan tanggal dan waktu
    is_active = models.BooleanField(null=True, blank=True)  # Menggunakan BooleanField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Form"
        verbose_name_plural = "Forms"  # Perbaiki plural form

    def __str__(self):
        return f'{self.name} - {self.tahun}'

class Pertanyaan(models.Model):
    QUESTION_CATEGORY_CHOICES = [
        ('baku', 'Baku'),
        ('spesifik', 'Spesifik'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('text', 'Teks'),
        ('multiple', 'Pilihan Ganda'),
        ('checkbox', 'Checkbox'),
        ('date', 'Tanggal'),
        ('likert', 'Skala Likert'),
        ('multi-select', 'Pilih Banyak'),
        ('file', 'Unggah File'),
        ('rating', 'Rating'),
        ('long-text', 'Teks Panjang'),
    ]

    name = models.TextField()
    indikator = models.ForeignKey(Indikator, on_delete=models.CASCADE, null=True, blank=True, related_name='pertanyaan')
    type = models.CharField(max_length=12, choices=QUESTION_TYPE_CHOICES)
    category = models.CharField(max_length=12, choices=QUESTION_CATEGORY_CHOICES)
    description = models.TextField(null=True, blank=True)
    evaluation_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pertanyaan"
        verbose_name_plural = "Pertanyaan"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.type} - {self.text}"

class FilePertanyaan(models.Model):
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='files_pertanyaan')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    encrypted_filename = models.CharField(max_length=255)
    file_extension = models.CharField(max_length=10)
    size = models.PositiveIntegerField()
    url = models.URLField(max_length=200)
    path = models.TextField()
    # content_type = models.CharField(max_length=50)
    content_type = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "File Pertanyaan"
        verbose_name_plural = "File Pertanyaan"

    def __str__(self):
        return f"File untuk {self.pertanyaan.text}"
    
    def save(self, *args, **kwargs):
        # Ubah nama file sebelum menyimpan
        if self.encrypted_filename:
            # Set the file name to the new encrypted_filename
            self.file.name = self.encrypted_filename
        super().save(*args, **kwargs)

class MasterPilihan(models.Model):
    name = models.CharField(max_length=255)
    bobot = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'bobot'], name='unique_name_bobot')
        ]

    def __str__(self):
        return self.name  # Corrected from `self.text` to `self.name`

class Pilihan(models.Model):
    master_pilihan = models.ForeignKey(MasterPilihan, on_delete=models.CASCADE, related_name='pilihan')
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='pilihan')
    bobot = models.DecimalField(max_digits=5, decimal_places=2)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pilihan"
        verbose_name_plural = "Pilihan"
        ordering = ['order'] 

    def __str__(self):
        return f"{self.master_pilihan.text} - {self.pertanyaan.text} (Bobot: {self.bobot})"

class PertanyaanInstansi(models.Model):
    QUESTION_CATEGORY_CHOICES = [
        ('baku', 'Baku'),
        ('spesifik', 'Spesifik'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('text', 'Teks'),
        ('multiple', 'Pilihan Ganda'),
        ('checkbox', 'Checkbox'),
        ('date', 'Tanggal'),
        ('likert', 'Skala Likert'),
        ('multi-select', 'Pilih Banyak'),
        ('file', 'Unggah File'),
        ('rating', 'Rating'),
        ('long-text', 'Teks Panjang'),
    ]

    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='pertanyaan_instansi')
    type = models.CharField(max_length=12, choices=QUESTION_TYPE_CHOICES)
    category = models.CharField(max_length=12, choices=QUESTION_CATEGORY_CHOICES)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='pertanyaan_instansi')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, null=True, blank=True, related_name='pertanyaan_instansi')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pertanyaan Instansi"
        verbose_name_plural = "Pertanyaan Instansi"
        ordering = ['order']

    def __str__(self):
        return f"Pertanyaan {self.pertanyaan.type} - {self.pertanyaan.name} {self.form.name} - {self.instansi.name} - Urutan: {self.order}"

class FilePertanyaanInstansi(models.Model):
    pertanyaan_instansi = models.ForeignKey(PertanyaanInstansi, on_delete=models.CASCADE, related_name='files_pertanyaan_instansi')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    encrypted_filename = models.CharField(max_length=255)
    file_extension = models.CharField(max_length=10)
    size = models.PositiveIntegerField()
    url = models.URLField(max_length=200)
    path = models.TextField()
    # content_type = models.CharField(max_length=50)
    content_type = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "File Pertanyaan Instansi"
        verbose_name_plural = "File Pertanyaan Instansi"

    def __str__(self):
        return f"File untuk {self.pertanyaan_instansi.pertanyaan.name}"
    
    def save(self, *args, **kwargs):
        # Ubah nama file sebelum menyimpan
        if self.encrypted_filename:
            # Set the file name to the new encrypted_filename
            self.file.name = self.encrypted_filename
        super().save(*args, **kwargs)

class Jawaban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jawaban')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, related_name='jawaban')
    pertanyaan_instansi = models.ForeignKey(PertanyaanInstansi, on_delete=models.CASCADE, related_name='jawaban')
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='jawaban')
    pilihan = models.ForeignKey(Pilihan, on_delete=models.CASCADE, null=True, blank=True, related_name='jawaban')
    text_jawaban = models.TextField(null=True, blank=True)
    bobot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Jawaban"
        verbose_name_plural = "Jawaban"

    def __str__(self):
        return f'{self.user} - {self.pertanyaan}'

class FileJawaban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, related_name='files')
    jawaban = models.ForeignKey(Jawaban, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    encrypted_filename = models.CharField(max_length=255)
    file_extension = models.CharField(max_length=10)
    size = models.PositiveIntegerField()
    url = models.URLField(max_length=200)
    path = models.TextField()
    # content_type = models.CharField(max_length=50)
    content_type = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "File Jawaban"
        verbose_name_plural = "File Jawaban"

    def __str__(self):
        return f"File untuk jawaban {self.jawaban.id}"
    
    def save(self, *args, **kwargs):
        # Ubah nama file sebelum menyimpan
        if self.encrypted_filename:
            # Set the file name to the new encrypted_filename
            self.file.name = self.encrypted_filename
        super().save(*args, **kwargs)

class Notifikasi(models.Model):
    TIPO_NOTIFIKASI_CHOICES = [
        ('jawaban', 'Jawaban'),
        ('verifikasi', 'Verifikasi'),
        ('perbarui', 'Perbarui'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifikasi')
    jawaban = models.ForeignKey(Jawaban, on_delete=models.CASCADE, null=True, blank=True, related_name='notifikasi')
    type = models.CharField(max_length=20, choices=TIPO_NOTIFIKASI_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"

    def __str__(self):
        return f'Notifikasi untuk {self.user} mengenai {self.jawaban}'

class JawabanFinal(models.Model):
    STATUS_CHOICES = [
        ('disetujui', 'Disetujui'),
        ('ditolak', 'Ditolak'),
        ('pending', 'Pending'),
    ]

    verifikator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifikator_jawaban_final')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_jawaban_final')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, related_name='jawaban_final')
    jawaban = models.ForeignKey(Jawaban, on_delete=models.CASCADE, related_name='jawaban_final')
    pilihan = models.ForeignKey(Pilihan, on_delete=models.SET_NULL, null=True, blank=True, related_name='jawaban_final')
    bobot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    catatan = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Jawaban Final"
        verbose_name_plural = "Jawaban Final"

    def __str__(self):
        return f'Final Jawaban oleh {self.user} - Status: {self.status}'

class UserLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "User Log"
        verbose_name_plural = "User Logs"

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

class JawabanHistori(models.Model):
    jawaban = models.ForeignKey(Jawaban, on_delete=models.CASCADE, related_name='jawaban_histori')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jawaban_histori')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, related_name='jawaban_histori')
    pertanyaan_instansi = models.ForeignKey(PertanyaanInstansi, on_delete=models.CASCADE, related_name='jawaban_histori')
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='jawaban_histori')
    pilihan = models.ForeignKey(Pilihan, on_delete=models.CASCADE, null=True, blank=True, related_name='jawaban_histori')
    text_jawaban = models.TextField(null=True, blank=True)
    bobot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Jawaban Histori"
        verbose_name_plural = "Jawaban Histori"

    def __str__(self):
        return f'{self.user} - {self.pertanyaan}'

class JawabanFinalHistori(models.Model):
    STATUS_CHOICES = [
        ('disetujui', 'Disetujui'),
        ('ditolak', 'Ditolak'),
        ('pending', 'Pending'),
    ]

    jawaban_final = models.ForeignKey(JawabanFinal, on_delete=models.CASCADE, related_name='jawaban_final_histori')
    verifikator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifikator_jawaban_final_histori')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_jawaban_final_histori')
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, related_name='jawaban_final_histori')
    jawaban = models.ForeignKey(Jawaban, on_delete=models.CASCADE, related_name='jawaban_final_histori')
    pilihan = models.ForeignKey(Pilihan, on_delete=models.SET_NULL, null=True, blank=True, related_name='jawaban_final_histori')
    bobot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    catatan = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Jawaban Final Histori"
        verbose_name_plural = "Jawaban Final Histori"

    def __str__(self):
        return f'Histori Final Jawaban oleh {self.user} - Status: {self.status}'
    
class FileVersion(models.Model):
    FILE_TYPE_CHOICES = [
        ('manual', 'Buku Panduan'),
        ('guide', 'Petunjuk Teknis'),
    ]

    file_name = models.CharField(max_length=255)  # Nama asli file
    file = models.FileField(upload_to='uploads/')  # Menyimpan file yang diupload
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)  # Menentukan jenis file
    version = models.PositiveIntegerField(default=1)  # Versi file
    is_active = models.BooleanField(default=True)  # Menandai apakah versi ini aktif
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Waktu file diupload
    original_filename = models.CharField(max_length=255)  # Nama asli file sebelum dienkripsi
    encrypted_filename = models.CharField(max_length=255)  # Nama file setelah dienkripsi
    file_extension = models.CharField(max_length=10)  # Ekstensi file (misalnya .pdf, .jpg)
    size = models.PositiveIntegerField()  # Ukuran file dalam byte
    url = models.URLField(max_length=200)  # URL untuk mengakses file jika disimpan di cloud
    path = models.TextField()  # Path lokal untuk file jika disimpan di server lokal
    content_type = models.TextField()  # Tipe konten dari file (misalnya, 'application/pdf')
    created_at = models.DateTimeField(auto_now_add=True)  # Waktu pembuatan file
    updated_at = models.DateTimeField(auto_now=True)  # Waktu terakhir file diperbarui
    deleted_at = models.DateTimeField(null=True, blank=True)  # Waktu file dihapus (soft delete)

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"
        ordering = ['-version']  # Urutkan berdasarkan versi terbaru

    def __str__(self):
        return f"{self.file_name} v{self.version} ({self.file_type})"

    def save(self, *args, **kwargs):
        """
        Menyimpan file dengan nama terenkripsi.
        Pastikan field `encrypted_filename` sudah diset sebelum disimpan.
        """
        if self.encrypted_filename:
            # Ubah nama file sebelum menyimpan ke dalam database
            self.file.name = self.encrypted_filename
        super().save(*args, **kwargs)

    # @classmethod
    # def set_active_version(cls, file_name, version, file_type=None):
    #     """
    #     Menetapkan versi tertentu sebagai versi aktif untuk jenis file tertentu.
    #     Nonaktifkan versi aktif lainnya untuk file yang sama.
    #     """
    #     # Membuat filter dasar
    #     filters = {'file_name': file_name, 'version': version}
    #     if file_type:
    #         filters['file_type'] = file_type

    #     # Nonaktifkan versi aktif lainnya untuk file_name yang sama dan tipe file
    #     cls.objects.filter(is_active=True, file_name=file_name, **filters).update(is_active=False)

    #     # Set versi yang dimaksud sebagai aktif
    #     cls.objects.filter(file_name=file_name, version=version, **filters).update(is_active=True)
