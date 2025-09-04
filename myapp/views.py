from django.views import View
from .models import (
    Instansi, User, Klaster, Indikator,
    Form, MasterPilihan, Pertanyaan, FilePertanyaan, PertanyaanInstansi, FilePertanyaanInstansi, FileJawaban, Pilihan, Jawaban,
    Notifikasi, JawabanFinal, UserLog, JawabanHistori, JawabanFinalHistori, FileVersion
)
from .forms import (
    InstansiForm, UserForm, KlasterForm, IndikatorForm,
    FormForm, PertanyaanForm, PilihanForm, JawabanForm,
    NotifikasiForm, JawabanFinalForm, UserLogForm, LoginForm
)
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.conf import settings
from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from datetime import datetime
import os, random, string, re, uuid
from mimetypes import guess_type
from django.http import JsonResponse, HttpResponse,Http404
from django.db.models import F
from django.db.models import Value
from django.db.models.functions import Concat
from django.db.models import Count
from django.db.models import Subquery, OuterRef
from django.core.paginator import Paginator

def is_superadmin(user):
    return user.is_superuser  # Memeriksa jika pengguna adalah superuser

def is_admin(user):
    return hasattr(user, 'role') and user.role == 'admin'  # Memeriksa role

def is_verifikator(user):
    return hasattr(user, 'role') and user.role == 'verifikator'  # Memeriksa role

def is_user(user):
    return hasattr(user, 'role') and user.role == 'user'  # Memeriksa role

def is_operator(user):
    return hasattr(user, 'role') and user.role == 'operator'  # Memeriksa role

class UserRegisterView(View):
    def get(self, request):
        return render(request, 'user/register.html')  # Ganti dengan template yang sesuai

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah ada.')
            return redirect('register')  # Ganti dengan URL yang sesuai

        user = User(username=username, email=email)
        user.set_password(password)  # Ini meng-hash password
        user.save()
        
        messages.success(request, 'User berhasil dibuat.')
        return redirect('login')  # Ganti dengan URL login Anda

class UserLoginView(View):
    def get(self, request):
        # Generate a new CAPTCHA
        captcha_key = CaptchaStore.generate_key()
        captcha_image_url_value = captcha_image_url(captcha_key)
        
        return render(request, 'auth/login.html', {
            'captcha_key': captcha_key,
            'captcha_image_url': captcha_image_url_value
        })

    def post(self, request):
        email = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        captcha_response = request.POST.get('captcha_response')
        captcha_key = request.POST.get('captcha_key')
        User = get_user_model()

        # Validasi CAPTCHA
        try:
            captcha_obj = CaptchaStore.objects.get(hashkey=captcha_key)
            if captcha_obj.challenge != captcha_response:
                messages.error(request, "CAPTCHA salah.")
                return self.render_login_page(request, email)
        except CaptchaStore.DoesNotExist:
            messages.error(request, "CAPTCHA tidak valid.")
            return self.render_login_page(request, email)

        try:
            user = User.objects.get(email=email, role=role)

            # Periksa apakah user aktif
            if not user.is_active:
                messages.error(request, "Akun Anda tidak aktif.")
                return self.render_login_page(request, email)

            if user.check_password(password):
                login(request, user)
                return self.redirect_user(request, user, email)

            messages.error(request, "Email atau password salah.")
        except User.DoesNotExist:
            messages.error(request, "Pengguna dengan email dan role tersebut tidak ditemukan.")

        return self.render_login_page(request, email)

    def render_login_page(self, request, email):
        # Menghasilkan CAPTCHA baru jika ada kesalahan
        captcha_key = CaptchaStore.generate_key()
        captcha_image_url_value = captcha_image_url(captcha_key)
        return render(request, 'auth/login.html', {
            'email': email,
            'captcha_image_url': captcha_image_url_value,
            'captcha_key': captcha_key
        })

    def redirect_user(self, request, user, email):
        # Redirect berdasarkan role pengguna
        if user.role == 'admin':
            return redirect('admin_dashboard')
        elif user.role == 'verifikator':
            return redirect('verifikator_dashboard')
        elif user.role == 'user':
            if not user.instansi:
                messages.error(request, "Instansi belum ditetapkan.")
                return self.render_login_page(request, email)
            else:
                return redirect('user_dashboard')
        elif user.role == 'operator':
            if not user.instansi:
                messages.error(request, "Instansi belum ditetapkan.")
                return self.render_login_page(request, email)
            else:
                return redirect('operator_dashboard')
        return redirect('dashboard')

User = get_user_model()

class PasswordResetRequestView(View):
    def get(self, request):
        return render(request, 'auth/password_reset.html')

    def post(self, request):
        email = request.POST.get('email')
        print(f'Received password reset request for email: {email}')

        if not email:
            messages.error(request, 'Email tidak boleh kosong.')
            return redirect('password_reset')

        try:
            user = User.objects.get(email=email)
            print(f'User found: {user.email}')

            # Generate a random reset code
            reset_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            print(f'Generated reset code: {reset_code}')

            # Save the reset code to the user or a related model (or send via email)
            # user.reset_code = reset_code  # Assuming you have a field in User model
            user.set_password(reset_code)
            user.save()

            # Send email with the reset code
            # send_mail(
            #     'Reset Password Code',
            #     f'Gunakan kode berikut untuk mereset password Anda: {reset_code}',
            #     settings.EMAIL_HOST_USER,
            #     [email],
            #     fail_silently=False,
            # )
            subject = "Reset Password Code"
            message = "Gunakan kode berikut untuk mereset password Anda: "+reset_code
            from_email =  settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, html_message=None)
            messages.success(request, 'Kode reset password telah dikirim ke email Anda.')
            print(f'Password reset code sent to {email}')

        except User.DoesNotExist:
            print(f'Password reset attempted for non-existent email: {email}')
            messages.error(request, 'Email tidak ditemukan.')
        except Exception as e:
            print(f'Error sending password reset code: {e}')
            messages.error(request, 'Terjadi kesalahan saat mengirim email. Silakan coba lagi.')

        return redirect('login')

class PasswordResetConfirmView(View):
    def get(self, request):
        return render(request, 'auth/password_reset_confirm.html')

    def post(self, request):
        email = request.POST.get('email')
        reset_code = request.POST.get('reset_code')
        new_password = request.POST.get('new_password')

        try:
            user = User.objects.get(email=email)
            if user.reset_code == reset_code:
                user.set_password(new_password)
                user.reset_code = None  # Clear the reset code
                user.save()
                messages.success(request, 'Password berhasil diubah.')
                return redirect('login')
            else:
                messages.error(request, 'Kode reset tidak valid.')
        except User.DoesNotExist:
            messages.error(request, 'Email tidak ditemukan.')

        return redirect('password_reset_confirm')

@method_decorator(login_required, name='dispatch')
class MyProtectedView(View):
    def get(self, request, *args, **kwargs):
        data = {"message": "This is a protected view."}
        return JsonResponse(data)

# Contoh untuk mendapatkan data user yang login
class UserProfileView(View):
    def get(self, request):
        user = request.user  # Mendapatkan data pengguna yang login
        return render(request, 'dashboard/profile.html', {'user': user})

class LogoutView(LogoutView):
    def get_next_page(self):
        messages.info(self.request, "Anda telah berhasil logout.")
        return super().get_next_page()
    
# Dashboard
@method_decorator(login_required, name='dispatch')
class AdminDashboardView(View):
    def get(self, request):
        manual = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual",is_active=True).order_by('-id','-version')
        guide = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide",is_active=True).order_by('-id','-version')
        return render(request, 'dashboard/admin_dashboard.html',{'manual':manual,'guide':guide})  # Ganti dengan nama template dashboard Anda

@method_decorator(login_required, name='dispatch')
class VerifikatorDashboardView(View):
    def get(self, request):
        manual = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual",is_active=True).order_by('-id','-version')
        guide = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide",is_active=True).order_by('-id','-version')
        return render(request, 'dashboard/verifikator_dashboard.html',{'manual':manual,'guide':guide})  # Ganti dengan nama template dashboard Anda

@method_decorator(login_required, name='dispatch')
class UserDashboardView(View):
    def get(self, request):
        manual = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual",is_active=True).order_by('-id','-version')
        guide = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide",is_active=True).order_by('-id','-version')
        return render(request, 'dashboard/user_dashboard.html',{'manual':manual,'guide':guide})  # Ganti dengan nama template dashboard Anda
    
@method_decorator(login_required, name='dispatch')
class OperatorDashboardView(View):
    def get(self, request):
        manual = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual",is_active=True).order_by('-id','-version')
        guide = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide",is_active=True).order_by('-id','-version')
        return render(request, 'dashboard/operator_dashboard.html',{'manual':manual,'guide':guide})  # Ganti dengan nama template dashboard Anda

# Notifikasi
# @csrf_exempt
# @login_required
class NotifikasiListViewNew(View):
    def get(self, request):
         # Ambil notifikasi yang berkaitan dengan jawaban yang dibuat oleh user
        notifikasi_user = Notifikasi.objects.filter(user=request.user).order_by('-created_at')
            
        # Ambil notifikasi yang berkaitan dengan jawaban yang telah diverifikasi
        jawaban_user = Jawaban.objects.filter(user=request.user)
        verifikasi_notifikasi = Notifikasi.objects.filter(
            jawaban__in=jawaban_user,
            type='verifikasi'
        ).order_by('-created_at')

        # Gabungkan kedua queryset
        notifikasi = notifikasi_user | verifikasi_notifikasi
        notifikasi = notifikasi.distinct().order_by('-created_at')

        data = []

        return render(request, 'data/notifikasi_list.html', {
            'data': data,
            'notifikasi': notifikasi, 
            'title': 'Notifikasi'
        })
    
# Pengguna Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PenggunaListView(View):
    def get(self, request):
        data = User.objects.all()
        instansi = Instansi.objects.exclude(deleted_at__isnull=False).values('id', 'name').order_by('name')
        return render(request, 'pengguna/pengguna.html', {
            'data': data,
            'instansi': instansi,
            'title': 'Pengguna'  # Add the title here
        })

# Instansi Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class InstansiListView(View):
    def get(self, request):
        data = Instansi.objects.all()
        return render(request, 'instansi/instansi.html', {
            'data': data,
            'title': 'Instansi'  # Add the title here
        })

# Master Pilihan Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class MasterPilihanListView(View):
    def get(self, request):
        data = MasterPilihan.objects.all()
        return render(request, 'master_pilihan/master_pilihan.html', {
            'data': data,
            'title': 'Master Pilihan'  # Add the title here
        })
    
# Pertanyaan Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PertanyaanListView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'pertanyaan/pertanyaan.html', {
            'data': data,
            'title': 'Pertanyaan'  # Add the title here
        })
    
# Buku Panduan Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class BukuPanduanListView(View):
    def get(self, request):
        data = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual")
        return render(request, 'buku_panduan/buku_panduan.html', {
            'data': data,
            'title': 'Buku Panduan'  # Add the title here
        })
    
# Petunjuk Teknis Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PetunjukTeknisListView(View):
    def get(self, request):
        data = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide")
        return render(request, 'petunjuk_teknis/petunjuk_teknis.html', {
            'data': data,
            'title': 'Petunjuk Teknis'  # Add the title here
        })

# Pilihan Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PilihanListView(View):
    def get(self, request):
        data = Pilihan.objects.all()
        pertanyaan = Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id','name', 'type').order_by('id')
        masterpilihan = MasterPilihan.objects.exclude(deleted_at__isnull=False).values('id','name', 'bobot').order_by('id')
        return render(request, 'pilihan/pilihan.html', {
            'data': data,
            'pertanyaan': pertanyaan,
            'masterpilihan': masterpilihan,
            'title': 'Pilihan Pertanyaan'  # Add the title here
        })

# Form Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class FormListView(View):
    def get(self, request):
        data = Form.objects.all()
        return render(request, 'form/form.html', {
            'data': data,
            'title': 'Form'  # Add the title here
        })

# Pertanyaan Baku Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PertanyaanBakuListView(View):
    def get(self, request):
        data = PertanyaanInstansi.objects.filter(category='baku',deleted_at__isnull=True)
        return render(request, 'pertanyaan_baku/pertanyaan_baku.html', {
            'data': data,
            'title': 'Pertanyaan Baku'  # Add the title here
        })

# Pertanyaan Spesifik Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class PertanyaanSpesifikListView(View):
    def get(self, request):
        data = PertanyaanInstansi.objects.filter(category='baku',deleted_at__isnull=True)
        return render(request, 'pertanyaan_spesifik/pertanyaan_spesifik.html', {
            'data': data,
            'title': 'Pertanyaan Spesifik'  # Add the title here
        })

# Data Views
@method_decorator(login_required, name='dispatch')
class dataSpesifikView(View):
    def get(self, request):
        # current_year = timezone.now().year
        form = Form.objects.filter(is_active=True)
        if form.exists():  # Check if there are any active forms
            current_year = form.first().year  # Get the year of the first active form
        else:
            current_year = None  # Handle the case where there are no active forms

        instansi = request.user.instansi_id  # Example of getting user_id from session
        
        # Filter data for the logged-in user and the current year
        data = PertanyaanInstansi.objects.filter(
            instansi=instansi, form__year=current_year, category='spesifik', deleted_at__isnull=True
        ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan').prefetch_related('files_pertanyaan_instansi')

        # Set up pagination
        paginator = Paginator(data, 1)  # Show 10 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Mendapatkan tahun saat ini
        year = timezone.now().year  # Menggunakan datetime untuk mendapatkan tahun

        # Mendapatkan form yang sesuai dengan tahun saat ini
        form = Form.objects.filter(year=year).first()

        return render(request, 'data/data_spesifik.html', {\
            'page_obj': page_obj,
            'form': form,
            'title': 'Data Spesifik'  # Add the title here
        })
    
# Data Views
@method_decorator(login_required, name='dispatch')
class dataBakuView(View):
    def get(self, request):
        # current_year = timezone.now().year
        form = Form.objects.filter(is_active=True)
        if form.exists():  # Check if there are any active forms
            current_year = form.first().year  # Get the year of the first active form
        else:
            current_year = None  # Handle the case where there are no active forms

        instansi = request.user.instansi_id  # Example of getting user_id from session
        
        # Filter data for the logged-in user and the current year
        data = PertanyaanInstansi.objects.filter(
            instansi=instansi, form__year=current_year, category='baku', deleted_at__isnull=True
        ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan').prefetch_related('files_pertanyaan_instansi')

        # Set up pagination
        paginator = Paginator(data, 1)  # Show 10 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Mendapatkan tahun saat ini
        year = timezone.now().year  # Menggunakan datetime untuk mendapatkan tahun

        # Mendapatkan form yang sesuai dengan tahun saat ini
        form = Form.objects.filter(year=year).first()

        return render(request, 'data/data_baku.html', {\
            'page_obj': page_obj,
            'form': form,
            'title': 'Data Baku'  # Add the title here
        })

# @method_decorator(login_required, name='dispatch')
# class dataBakuView(View):
#     def get(self, request):
#         data = Pertanyaan.objects.all()
#         return render(request, 'data/data_baku.html', {
#             'data': data,
#             'title': 'Data Baku'  # Add the title here
#         })

@method_decorator(login_required, name='dispatch')
class hasilAkumulasiView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/hasil_akumulasi.html', {
            'data': data,
            'title': 'Hasil Akumulasi'  # Add the title here
        })

@method_decorator(login_required, name='dispatch')
class lihatHasilView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/lihat_hasil.html', {
            'data': data,
            'title': 'Lihat Hasil'  # Add the title here
        })
    
@method_decorator(login_required, name='dispatch')
class dataGeneralDetailView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/data_general_detail.html', {
            'data': data,
            'title': 'Data General Detail'  # Add the title here
        })

@method_decorator(login_required, name='dispatch')
class penilaianPerangkatDaerahDetailView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/penilaian_perangkat_daerah_detail.html', {
            'data': data,
            'title': 'Data Penilaian Perangkat Daerah Detail'  # Add the title here
        })

@method_decorator(login_required, name='dispatch')
class penilaianPerangkatDaerahView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/penilaian_perangkat_daerah.html', {
            'data': data,
            'title': 'Penilaian Perangkat Daerah'  # Add the title here
        })
    
@method_decorator(login_required, name='dispatch')
class dataGeneralView(View):
    def get(self, request):
        data = Pertanyaan.objects.all()
        return render(request, 'data/data_general.html', {
            'data': data,
            'title': 'Data General'  # Add the title here
        })

# Fungsi untuk memvalidasi nama
def validate_name(name):
    if len(name) < 3 or len(name) > 10000:
        raise ValidationError(_('Nama harus terdiri dari 3 hingga 10000 karakter.'))

# Fungsi untuk memvalidasi username
def validate_username(username):
    # Pastikan username tidak kosong dan panjangnya antara 8 hingga 30 karakter
    if len(username) < 8 or len(username) > 30:
        raise ValidationError(_('Username harus terdiri dari 8 hingga 30 karakter.'))
    
    # Pastikan username hanya terdiri dari huruf, angka, dan karakter tertentu
    if not username.isalnum() and not all(c in ['_', '-'] for c in username):
        raise ValidationError(_('Username hanya boleh mengandung huruf, angka, underscore (_), dan tanda hubung (-).'))
    
# Fungsi untuk memvalidasi email
def validate_email(email):
    # Pastikan email tidak kosong
    if not email:
        raise ValidationError(_('Email tidak boleh kosong.'))
    
    # Gunakan regex untuk memvalidasi format email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValidationError(_('Format email tidak valid.'))

# Fungsi untuk memvalidasi password
def validate_password(password):
    # Pastikan kata sandi tidak kosong
    if not password:
        raise ValidationError(_('Kata sandi tidak boleh kosong.'))

    # Memeriksa panjang kata sandi
    if len(password) < 8:
        raise ValidationError(_('Kata sandi harus terdiri dari minimal 8 karakter.'))

    # Memeriksa apakah kata sandi mengandung huruf besar
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_('Kata sandi harus mengandung setidaknya satu huruf besar.'))

    # Memeriksa apakah kata sandi mengandung huruf kecil
    if not re.search(r'[a-z]', password):
        raise ValidationError(_('Kata sandi harus mengandung setidaknya satu huruf kecil.'))

    # Memeriksa apakah kata sandi mengandung angka
    if not re.search(r'[0-9]', password):
        raise ValidationError(_('Kata sandi harus mengandung setidaknya satu angka.'))

    # Memeriksa apakah kata sandi mengandung karakter khusus
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_('Kata sandi harus mengandung setidaknya satu karakter khusus.'))

# Fungsi untuk memvalidasi role
def validate_role(role):
    # Daftar peran yang valid
    valid_roles = ['admin', 'verifikator', 'user', 'operator']  # Sesuaikan dengan peran yang Anda miliki

    # Pastikan role tidak kosong
    if not role:
        raise ValidationError(_('Peran tidak boleh kosong.'))

    # Pastikan role ada dalam daftar peran yang valid
    if role not in valid_roles:
        raise ValidationError(_('Peran tidak valid. Pilih salah satu dari: %s.' % ', '.join(valid_roles)))

# Fungsi untuk memvalidasi instansi
def validate_instansi(instansi_id):
    # Pastikan instansi_id tidak kosong
    if not instansi_id:
        raise ValidationError(_('Instansi tidak boleh kosong.'))

    # Pastikan instansi dengan ID tersebut ada di database
    if not Instansi.objects.filter(id=instansi_id).exists():
        raise ValidationError(_('Instansi dengan ID %s tidak ditemukan.' % instansi_id))

# # Fungsi untuk memvalidasi id
# def validate_id(object_id, model_class):
#     # Pastikan object_id tidak kosong
#     if object_id is None or object_id == '':
#         raise ValidationError(_('ID tidak boleh kosong.'))

#     # Coba mengonversi input ke integer
#     try:
#         object_id = int(object_id)
#     except ValueError:
#         raise ValidationError(_('ID harus berupa angka bulat.'))

#     # Pastikan model_class adalah kelas model yang valid
#     if not isinstance(model_class, type) or not hasattr(model_class, 'objects'):
#         raise ValidationError(_('Model tidak valid.'))
    
#     # Convert the ID to an integer
#     try:
#         object_id = int(object_id)
#     except ValueError:
#         raise ValueError("ID harus berupa angka bulat.")

#     # Try to retrieve the Pertanyaan instance
#     try:
#         model_instance = model_class.objects.get(id=object_id)
#     except ObjectDoesNotExist:
#         raise ValueError(f"Pertanyaan dengan ID {object_id} tidak ditemukan.")

#     # Pastikan ID ada di database
#     if not model_class.objects.filter(id=object_id).exists():
#         raise ValidationError(_('ID %s tidak ditemukan.' % object_id))

def validate_id(object_id, model_class):
    # Ensure object_id is not empty
    if object_id is None or object_id == '':
        raise ValidationError(_('ID tidak boleh kosong.'))

    # Try to convert input to integer
    try:
        object_id = int(object_id)
    except ValueError:
        raise ValidationError(_('ID harus berupa angka bulat.'))

    # Validate model_class
    if not isinstance(model_class, type) or not hasattr(model_class, 'objects'):
        raise ValidationError(_('Model tidak valid.'))

    # Try to retrieve the model instance
    try:
        model_instance = model_class.objects.get(id=object_id)
    except model_class.DoesNotExist:
        print(model_class)
        raise ValidationError(_('ID %s tidak ditemukan.' % object_id))

    return model_instance  # Optionally return the found instance


# Fungsi untuk memvalidasi double
def validate_double(value):
    try:
        # Attempt to convert the value to a float (which is double in Python)
        double_value = float(value)
        return True, double_value
    except ValueError:
        return False, None
    
# Fungsi untuk memvalidasi integer
def validate_integer(value):
    try:
        # Attempt to convert the value to an integer
        int_value = int(value)
        return True, int_value
    except ValueError:
        return False, None

# Fungsi untuk memvalidasi type pertanyaan
def validate_type_pertanyaan(role):
    # Daftar peran yang valid
    valid_roles = ['text', 'multiple','checkbox','date','likert','multi-select','file','rating','long-text']  # Sesuaikan dengan peran yang Anda miliki

    # Pastikan role tidak kosong
    if not role:
        raise ValidationError(_('Jenis tidak boleh kosong.'))

    # Pastikan role ada dalam daftar peran yang valid
    if role not in valid_roles:
        raise ValidationError(_('Jenis tidak valid. Pilih salah satu dari: %s.' % ', '.join(valid_roles)))
    
# Fungsi untuk memvalidasi category pertanyaan
def validate_category_pertanyaan(role):
    # Daftar peran yang valid
    valid_roles = ['baku', 'spesifik']  # Sesuaikan dengan peran yang Anda miliki

    # Pastikan role tidak kosong
    if not role:
        raise ValidationError(_('Kategori tidak boleh kosong.'))

    # Pastikan role ada dalam daftar peran yang valid
    if role not in valid_roles:
        raise ValidationError(_('Kategori tidak valid. Pilih salah satu dari: %s.' % ', '.join(valid_roles)))

# Fungsi untuk memvalidasi tahun
def validate_year(value):
    try:
        # Attempt to convert the value to an integer
        year = int(value)
        
        # Get the current year
        current_year = datetime.now().year
        
        # Check if the year is in a valid range
        if 1900 <= year <= current_year:
            return True, year
        else:
            return False, None
    except ValueError:
        return False, None

# Fungsi untuk memvalidasi type pertanyaan pilihan
def validate_type_pertanyaan_pilihan(role):
    # Daftar peran yang valid
    valid_roles = ['multiple','checkbox','likert','multi-select','rating']  # Sesuaikan dengan peran yang Anda miliki

    # Pastikan role tidak kosong
    if not role:
        raise ValidationError(_('Jenis tidak boleh kosong.'))

    # Pastikan role ada dalam daftar peran yang valid
    if role not in valid_roles:
        raise ValidationError(_('Jenis tidak valid. Pilih salah satu dari: %s.' % ', '.join(valid_roles)))

def get_questionsTest(request):
    instansi = request.user.instansi  # Atur sesuai logika Anda
    # current_year = timezone.now().year  # Menggunakan timezone untuk mendapatkan tahun saat ini
    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms
    data = PertanyaanInstansi.objects.filter(
        instansi=instansi, form__year=current_year, category='spesifik', deleted_at__isnull=True
    ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan', 'files_pertanyaan_instansi')

    # Ambil jawaban yang sudah ada untuk pengguna ini
    jawaban = Jawaban.objects.filter(user=request.user,deleted_at__isnull=True).select_related('pertanyaan', 'pilihan')

    # Buat dictionary untuk menyimpan jawaban yang sudah ada
    jawaban_dict = {j.pertanyaan.id: j for j in jawaban}

    # Buat response JSON
    questions = []
    for q in data:
        files = [{
            "id": f.id,
            "encrypted_filename": f.encrypted_filename
        } for f in q.files_pertanyaan_instansi.filter(deleted_at__isnull=True)]
        answered_file = None

        choices = [{"id": p.id, "name": p.master_pilihan.name, "bobot": int(p.master_pilihan.bobot)} for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True).order_by('order')]
        answered_choice = None
        
        # Cek apakah ada jawaban untuk pertanyaan ini
        if q.pertanyaan.id in jawaban_dict:
            answered_choice = jawaban_dict[q.pertanyaan.id].pilihan.id

        questions.append({
            "order": q.order,
            "pertanyaan_instansi_id": q.id,
            "pertanyaan_id": q.pertanyaan_id,
            "pertanyaan_description": q.pertanyaan.description,
            "pertanyaan_file" : files,
            "name": q.pertanyaan.name,
            "choices": choices,
            "answered_choice": answered_choice  # Menyimpan pilihan yang sudah dijawab
        })

    return JsonResponse(questions, safe=False)

from django.http import JsonResponse
from django.utils import timezone

def get_questionsTest2(request):
    instansi = request.user.instansi
    # current_year = timezone.now().year
    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms
    data = PertanyaanInstansi.objects.filter(
        instansi=instansi, form__year=current_year, category='spesifik', deleted_at__isnull=True,
    ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan', 'files_pertanyaan_instansi')

    # Ambil jawaban yang sudah ada untuk pengguna ini
    jawaban = Jawaban.objects.filter(user=request.user, deleted_at__isnull=True).select_related('pertanyaan', 'pilihan')
    jawaban_dict = {j.pertanyaan.id: j for j in jawaban}

    questions = []
    question_ids = [q.id for q in data]  # List of question IDs to find next/prev
    for q in data:
        files = [{"id": f.id, "encrypted_filename": f.encrypted_filename} for f in q.files_pertanyaan_instansi.filter(deleted_at__isnull=True)]
        answered_choice = None
        
        choices = [
            {"id": p.id, "name": p.master_pilihan.name, "bobot": int(p.master_pilihan.bobot)}
            for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True).order_by('order')
        ]

        # Get answered choice if available
        if q.pertanyaan.id in jawaban_dict:
            answered_choice = jawaban_dict[q.pertanyaan.id].pilihan.id

        # Calculate max bobot
        max_bobot = round(max((p.master_pilihan.bobot for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True)), default=0), 2)

        # Determine previous and next question
        current_index = question_ids.index(q.id)
        prev_id = question_ids[current_index - 1] if current_index > 0 else None
        next_id = question_ids[current_index + 1] if current_index < len(question_ids) - 1 else None

        questions.append({
            "order": q.order,
            "pertanyaan_instansi_id": q.id,
            "pertanyaan_id": q.pertanyaan_id,
            "pertanyaan_description": q.pertanyaan.description,
            "pertanyaan_file": files,
            "name": q.pertanyaan.name,
            "choices": choices,
            "answered_choice": answered_choice,
            "max_bobot": max_bobot,  # Max bobot from choices
            "prev_question_id": prev_id,  # ID of the previous question
            "next_question_id": next_id,  # ID of the next question
        })

    return JsonResponse(questions, safe=False)

def get_questionsTest3(request):
    instansi = request.user.instansi
    # current_year = timezone.now().year
    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms
    data = PertanyaanInstansi.objects.filter(
        instansi=instansi, form__year=current_year, category='spesifik', deleted_at__isnull=True,
    ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan', 'files_pertanyaan_instansi')

    # Ambil jawaban yang sudah ada untuk pengguna ini
    jawaban = Jawaban.objects.filter(user=request.user, deleted_at__isnull=True).select_related('pertanyaan', 'pilihan')
    jawaban_dict = {j.pertanyaan.id: j for j in jawaban}

    # Get the current question ID from the query parameters, default to the first one
    current_question_id = request.GET.get('current_id')
    
    # Determine the index of the current question
    question_ids = [q.id for q in data]
    if current_question_id and current_question_id.isdigit() and int(current_question_id) in question_ids:
        current_index = question_ids.index(int(current_question_id))
    else:
        current_index = 0  # Start with the first question if no valid ID is provided

    # Get the current question
    q = data[current_index]
    files = [{"id": f.id, "encrypted_filename": f.encrypted_filename} for f in q.files_pertanyaan_instansi.filter(deleted_at__isnull=True)]
    answered_choice = None
    
    choices = [
        {"id": p.id, "name": p.master_pilihan.name, "bobot": int(p.master_pilihan.bobot)}
        for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True).order_by('order')
    ]

    # Get answered choice if available
    if q.pertanyaan.id in jawaban_dict:
        answered_choice = jawaban_dict[q.pertanyaan.id].pilihan.id

    # Calculate max bobot
    max_bobot = round(max((p.master_pilihan.bobot for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True)), default=0), 2)

    # Determine previous and next question IDs
    prev_id = question_ids[current_index - 1] if current_index > 0 else None
    next_id = question_ids[current_index + 1] if current_index < len(question_ids) - 1 else None

    question_data = {
        "order": q.order,
        "pertanyaan_instansi_id": q.id,
        "pertanyaan_id": q.pertanyaan_id,
        "pertanyaan_description": q.pertanyaan.description,
        "pertanyaan_file": files,
        "name": q.pertanyaan.name,
        "choices": choices,
        "answered_choice": answered_choice,
        "max_bobot": max_bobot,
        "prev_question_id": prev_id,
        "next_question_id": next_id,
    }

    return JsonResponse(question_data)

def get_questions(request):
    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms

    # current_year = timezone.now().year
    category = request.GET.get('category')
    if category == 'spesifik':
        instansi = request.GET.get('instansi')
    else:
        instansi = None

    data = PertanyaanInstansi.objects.filter(
        instansi=instansi, form__year=current_year, category=category, deleted_at__isnull=True,
    ).select_related('pertanyaan').prefetch_related('pertanyaan__pilihan', 'files_pertanyaan_instansi')

    # Ambil jawaban yang sudah ada untuk pengguna ini
    jawaban = Jawaban.objects.filter(user=request.user, deleted_at__isnull=True).select_related('pertanyaan', 'pilihan')
    jawaban_dict = {j.pertanyaan.id: j for j in jawaban}

    # Get the current question ID from the query parameters, default to the first one
    current_question_id = request.GET.get('current_id')
    
    # Determine the index of the current question
    question_ids = [q.id for q in data]
    if current_question_id and current_question_id.isdigit() and int(current_question_id) in question_ids:
        current_index = question_ids.index(int(current_question_id))
    else:
        current_index = 0  # Start with the first question if no valid ID is provided

    # Get the current question
    q = data[current_index]
    files = [{"id": f.id, "encrypted_filename": f.encrypted_filename} for f in q.files_pertanyaan_instansi.filter(deleted_at__isnull=True)]

    print(files)
    
    # Determine the choices based on the type of the question
    choices = []
    if q.pertanyaan.type == 'multiple':
        choices = [
            {"id": p.id, "name": p.master_pilihan.name, "bobot": int(p.master_pilihan.bobot), "is_multiple": True}
            for p in q.pertanyaan.pilihan.filter(deleted_at__isnull=True).order_by('order')
        ]


    # Get answered choice if available
    answered_final = None
    answered_choice = None
    if q.pertanyaan.id in jawaban_dict:
        jawaban_instance = jawaban_dict[q.pertanyaan.id]
        
        # Check if pilihan (choice) exists
        if jawaban_instance.pilihan:
            answered_choice = {
                "choice": jawaban_instance.pilihan.id,
                "bobot": round(jawaban_instance.bobot, 2),
                "text": jawaban_instance.text_jawaban or "",  # Provide a default value if text is None
                "files": [
                    {
                        "id": file_jawaban.id,
                        "original_name": file_jawaban.original_filename,
                        "encrypt_name": file_jawaban.encrypted_filename
                    } for file_jawaban in jawaban_instance.files.filter(deleted_at__isnull=True)
                ]
            }

           # Fetch jawaban_final with deleted_at = False
            jawaban_final_instance = jawaban_instance.jawaban_final.filter(deleted_at__isnull=True).first()

            if jawaban_final_instance:
                answered_final = {
                    "id": jawaban_final_instance.id,
                    "bobot": round(jawaban_final_instance.bobot, 2),
                    "catatan": jawaban_final_instance.catatan or 0,
                    "status": jawaban_final_instance.status or 0,
                    "pilihan_id": jawaban_final_instance.pilihan_id or 0,
                    "user_id": jawaban_final_instance.user_id or 0,
                    "history": [
                        {
                            "id": history.id,
                            "bobot": round(history.bobot, 2),
                            "catatan": history.catatan or 0,
                            "status": history.status or 0,
                            "pilihan_id": history.pilihan_id or 0,
                            "user_id": history.user_id or 0
                        } for history in jawaban_instance.jawaban_final.filter(deleted_at__isnull=False).order_by('-created_at')
                    ]
                }
        else:
            # Handle case where pilihan is None
            answered_choice = {
                "choice": None,
                "bobot": 0,
                "text": jawaban_instance.text_jawaban or "",  # Provide a default value if text is None
                "files": [
                    {
                        "id": file_jawaban.id,
                        "original_name": file_jawaban.original_filename,
                        "encrypt_name": file_jawaban.encrypted_filename
                    } for file_jawaban in jawaban_instance.files.filter(deleted_at__isnull=True)
                ]
            }

    # Calculate max bobot only if choices are available
    choices_queryset = q.pertanyaan.pilihan.filter(deleted_at__isnull=True)
    if choices_queryset.exists():
        max_bobot = round(max((p.master_pilihan.bobot for p in choices_queryset), default=0), 2)
    else:
        max_bobot = 0  # Or handle as needed

    # Determine previous and next question IDs
    prev_id = question_ids[current_index - 1] if current_index > 0 else None
    next_id = question_ids[current_index + 1] if current_index < len(question_ids) - 1 else None

    question_data = {
        "order": q.order,
        "pertanyaan_instansi_id": q.id,
        "pertanyaan_id": q.pertanyaan_id,
        "pertanyaan_description": q.pertanyaan.description,
        "pertanyaan_file": files,
        "name": q.pertanyaan.name,
        "choices": choices,
        "answered_choice": answered_choice,
        "answered_final": answered_final,
        "max_bobot": max_bobot,
        "prev_question_id": prev_id,
        "next_question_id": next_id,
    }

    return JsonResponse(question_data)


@csrf_exempt  # Use this if CSRF tokens are not being sent, but it's better to handle CSRF properly.
def save_choice(request):
    if request.method == 'POST':
        text_jawaban = request.POST.get('text')
        bobot = request.POST.get('bobot')
        pertanyaan_id = request.POST.get('question_id')
        pertanyaan_instansi_id = request.POST.get('question_instansi_id')
        pilihan_id = request.POST.get('choice_id')
        name = request.POST.get('name')
        user_id = request.user.id

        # Mendapatkan tahun saat ini
        year = timezone.now().year  # Menggunakan datetime untuk mendapatkan tahun

        # Mendapatkan form yang sesuai dengan tahun saat ini
        form = Form.objects.filter(year=year).first()

        # Mendapatkan waktu saat ini (timezone-aware)
        now = timezone.now()

        # Memeriksa apakah 'form.end' ada (tidak NULL) dan apakah waktu saat ini sudah melewati 'form.end'
        if form and form.end and form.end <= now:
            return JsonResponse({
                "success": False,
                "message": "Data gagal disimpan. Waktu pengisian telah berakhir"
            }, status=400)

        # Check if pilihan_id is valid
        if not pilihan_id or not Pilihan.objects.filter(id=pilihan_id).exists():
            pilihan_id = None  # Set pilihan_id to None if invalid or not found
            bobot = 0
        
        # Buat atau perbarui jawaban baru
        jawaban, created = Jawaban.objects.update_or_create(
            user=request.user,
            instansi=request.user.instansi,
            pertanyaan_id=pertanyaan_id,
            pertanyaan_instansi_id=pertanyaan_instansi_id,
            deleted_at=None,
            defaults={
                'text_jawaban': text_jawaban,
                'bobot': bobot,
                'pilihan_id': pilihan_id,
                'deleted_at': None  # Pastikan deleted_at untuk yang baru adalah None
            }
        )

        # Ambil notifikasi terbaru yang bertipe 'jawaban' atau 'perbarui'
        latest_notif = Notifikasi.objects.filter(
            jawaban=jawaban,
            type__in=['jawaban', 'perbarui']
        ).order_by('-created_at').first()  # Ambil yang terbaru

        # Cek apakah ada notifikasi verifikasi untuk jawaban ini
        verifikasi_notif = Notifikasi.objects.filter(
            jawaban=jawaban,
            type='verifikasi'
        ).order_by('-created_at').first()  # Ambil yang terbaru

        # Tentukan tipe notifikasi
        if verifikasi_notif:
            if not latest_notif or verifikasi_notif.created_at > latest_notif.created_at:
                notif_type = 'perbarui'  # Jika notifikasi verifikasi lebih baru
            else:
                notif_type = latest_notif.type  # Gunakan tipe jawaban yang terbaru
        else:
            notif_type = 'jawaban'  # Jika tidak ada notifikasi verifikasi

        # Buat notifikasi setelah jawaban disimpan
        if created:
            Notifikasi.objects.create(
                user=request.user,
                jawaban=jawaban,
                type=notif_type,
                is_read=False,
                created_at=timezone.now()  # Ini akan otomatis terisi
            )
            print("Notifikasi berhasil dibuat.")
        else:
            print("Jawaban diperbarui, tidak membuat notifikasi baru.")
            
        # Simpan histori jawaban jika jawaban diperbarui
        if not created:
            JawabanHistori.objects.create(
                user=jawaban.user,
                instansi=jawaban.instansi,
                pertanyaan_id=jawaban.pertanyaan_id,
                pertanyaan_instansi_id=jawaban.pertanyaan_instansi_id,
                jawaban=jawaban,
                text_jawaban=jawaban.text_jawaban,
                bobot=jawaban.bobot,
                pilihan_id=jawaban.pilihan_id,
                updated_at=timezone.now()
            )

        # Handle file uploads
        uploaded_file = request.FILES.get('file_input')  # Gunakan get untuk mendapatkan satu file

        # Validasi jika tidak ada file yang di-upload
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': 'Tidak ada file yang di-upload.'})

        # Validasi maksimum ukuran file
        max_file_size = 5 * 1024 * 1024  # 5 MB
        if uploaded_file.size > max_file_size:
            return JsonResponse({'success': False, 'error': 'Ukuran file tidak boleh lebih dari 5 MB.'})

        # Validasi panjang nama file
        max_filename_length = 255
        original_filename = uploaded_file.name
        if len(original_filename) > max_filename_length:
            return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})

        # Validasi panjang file extension
        max_file_extension_length = 10
        file_extension = os.path.splitext(original_filename)[1]
        if len(file_extension) > max_file_extension_length:
            return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

        try:
            # Generate a new unique filename using UUID
            unique_id = str(uuid.uuid4())
            new_filename = f"{unique_id}{file_extension}"
            original_filename = f"{name}{file_extension}"
                
            # Create a FileJawaban instance
            file_instance = FileJawaban(
                user=request.user,
                instansi=request.user.instansi,
                jawaban=jawaban,
                file=uploaded_file,
                original_filename=original_filename,
                encrypted_filename=new_filename,  # Gunakan nama file baru
                file_extension=file_extension,  # Extract file extension
                size=uploaded_file.size,
                content_type=uploaded_file.content_type,
            )
            file_instance.save()  # Simpan instance ke database
            return JsonResponse({"success": True, "message": "Data berhasil disimpan."})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({"success": False, "message": "Data gagal disimpan."}, status=400)

def save_correction(request):
    if request.method == 'POST':
        # Ambil data dari request
        catatan = request.POST.get('text')
        bobot = request.POST.get('bobot')
        jawaban_id = request.POST.get('answer_id')
        pilihan_id = request.POST.get('choice_id')
        jawaban_final_id = request.POST.get('final_id')
        status = request.POST.get('status')
        verifikator = request.user

        # Check if pilihan_id is valid
        if not pilihan_id or not Pilihan.objects.filter(id=pilihan_id).exists():
            pilihan_id = None  # Set pilihan_id to None if invalid or not found
            bobot = 0
        
        jawaban = Jawaban.objects.filter(id=jawaban_id).first()

        if not jawaban:
            return JsonResponse({"success": False, "message": "Jawaban tidak ditemukan."}, status=400)

        # Mengecek apakah ada jawaban_final dengan id tertentu
        cek_jawaban_final = JawabanFinal.objects.filter(id=jawaban_final_id).first()

        if cek_jawaban_final:
            # Jika jawaban_final_id ada, update entri yang ada
            cek_jawaban_final.verifikator = verifikator
            cek_jawaban_final.bobot = bobot
            cek_jawaban_final.catatan = catatan
            cek_jawaban_final.status = status  # Menambahkan status yang ingin diubah
            cek_jawaban_final.pilihan_id = pilihan_id  # Update pilihan_id
            cek_jawaban_final.save()  # Simpan perubahan
            print("Data berhasil diperbarui!")
            jawaban_final = cek_jawaban_final  # Menghubungkan variabel jawaban_final dengan yang sudah diupdate
            created = False
        else:
            # Jika jawaban_final_id tidak ada, buat data baru
            jawaban_final = JawabanFinal.objects.create(
                jawaban_id=jawaban_id,
                user=jawaban.user,
                instansi=jawaban.instansi,
                verifikator=verifikator,
                bobot=bobot,
                catatan=catatan,
                status=status,  # Status yang ingin Anda tentukan
                pilihan_id=pilihan_id  # Pilihan ID yang ingin ditambahkan
            )
            created = True
            print("Data baru berhasil dibuat!")

        # Membuat notifikasi
        notif_type = "verifikasi"
        Notifikasi.objects.create(
            user=request.user,
            jawaban=jawaban,
            type=notif_type,
            is_read=False,
            created_at=timezone.now()  # Ini akan otomatis terisi
        )

        # Simpan histori jika jawaban_final berhasil dibuat atau diperbarui
        if jawaban_final:
            JawabanFinalHistori.objects.create(
                jawaban_final=jawaban_final,  # Menyimpan foreign key ke jawaban_final
                jawaban_id=jawaban_final.jawaban_id,
                user=jawaban_final.user,
                instansi=jawaban_final.instansi,
                verifikator=jawaban_final.verifikator,
                bobot=jawaban_final.bobot,
                catatan=jawaban_final.catatan,
                status=jawaban_final.status,
                updated_at=timezone.now()  # Atau gunakan auto_now_add=True di model
            )

        return JsonResponse({"success": True, "message": "Data berhasil disimpan."})
    
    return JsonResponse({"success": False, "message": "Data gagal disimpan."}, status=400)

# Pengguna API
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def pengguna_data(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name').strip()
            username = request.POST.get('username').strip()
            email = request.POST.get('email').strip()
            password = request.POST.get('password').strip()
            role = request.POST.get('role').strip()
            instansi = request.POST.get('instansi').strip()

            name = escape(name)
            username = escape(username)
            email = escape(email)
            password = escape(password)
            role = escape(role)
            instansi = escape(instansi)

            # Validasi input
            try:
                validate_name(name)
                validate_username(username)
                validate_email(email)
                validate_password(password)
                validate_role(role)
                validate_instansi(instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            active = True
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email Pengguna sudah ada.'})
            new = User.objects.create(first_name=name,username=username,email=email,password=password,role=role,instansi_id=instansi,is_active=active)
            new.set_password(password)
            new.save()
            return JsonResponse({'success': True})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,User)
            except ValidationError as e:
                print(e)
                return JsonResponse({'success':False, 'message': str(e)})
            delete = User.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
            else:
                print('error')
        elif action == 'edit':
            id = request.POST.get('id','').strip()
            name = request.POST.get('name','').strip()
            name = request.POST.get('name','').strip()
            username = request.POST.get('username','').strip()
            email = request.POST.get('email','').strip()
            password = request.POST.get('password','').strip()
            role = request.POST.get('role','').strip()
            instansi = request.POST.get('instansi','').strip()
            id = escape(id)
            name = escape(name)
            username = escape(username)
            email = escape(email)
            password = escape(password)
            role = escape(role)
            instansi = escape(instansi)
            try:
                validate_id(id,User)
                validate_name(name)
                validate_username(username)
                validate_email(email)
                if password:
                    validate_password(password)
                validate_role(role)
                validate_instansi(instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            # Buat query untuk memperbarui user
            update_fields = {
                'first_name': name,
                'username': username,
                'email': email,
                'role': role,
                'instansi': instansi,
            }
            if password:
                update_fields['password'] = make_password(password)\
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if User.objects.filter(username=username, email=email).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Nama Pengguna sudah ada.'})
            User.objects.filter(id=id).update(**update_fields)
            return JsonResponse({'success': True})
        elif action == 'deactive':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,User)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            User.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'active':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,User)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            User.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'reset-password':
            id = request.POST.get('id').strip()
            email = request.POST.get('email').strip()
            username = request.POST.get('username').strip()
            new_password = request.POST.get('password').strip()
            id = escape(id)
            username = escape(username)
            email = escape(email)
            new_password = escape(new_password)
            try:
                validate_id(id,User)
                validate_username(username)
                validate_email(email)
                validate_password(new_password)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            user = User.objects.filter(id=id, email=email, username=username).first()
            if user:
                user.password = make_password(new_password)
                user.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Pengguna tidak ditemukan.'})
    data = list(User.objects.exclude(deleted_at__isnull=False).values('id', 'first_name','username','email','role','instansi_id','instansi__name','is_active','last_login').order_by('first_name'))
    for index, item in enumerate(data):
        item['no'] = index + 1
    return JsonResponse({'data': data})

from django.db.models import Q

def count_answers(pertanyaan_instansi_id, pertanyaan_id, user_id, instansi_id, category):
    # Ambil jawaban untuk user tertentu
    jawaban = (
        Jawaban.objects
        .filter(
            user_id=user_id,
            instansi_id=instansi_id,
            pertanyaan_instansi_id=pertanyaan_instansi_id,
            pertanyaan_id=pertanyaan_id,
            deleted_at__isnull=True
        )
        .values('id', 'text_jawaban', 'pilihan_id', 'bobot')  # Ambil id, text_jawaban, pilihan_id, dan bobot
    )

    # Inisialisasi hitungan
    count_same = 0
    count_different = 0
    total_bobot = 0

    # Jika tidak ada jawaban, kembalikan 0
    if not jawaban:
        return {
            'count_same': count_same,
            'count_different': count_different,
            'total_bobot': total_bobot
        }

    # Buat list dari jawaban_id dan pilihan_id untuk query yang lebih efisien
    jawaban_ids = [item['id'] for item in jawaban]
    pilihan_ids = [item['pilihan_id'] for item in jawaban]

    # Ambil semua JawabanFinal yang terkait dengan jawaban_ids dan pilihan_ids dalam satu query
    jawaban_final = JawabanFinal.objects.filter(
        Q(jawaban_id__in=jawaban_ids) & Q(pilihan_id__in=pilihan_ids) & Q(deleted_at__isnull=True)
    ).values('jawaban_id', 'pilihan_id','bobot','status')

    # Buat set untuk memeriksa JawabanFinal yang sesuai
    jawaban_final_set = {(item['jawaban_id'], item['pilihan_id']): {'status': item['status'], 'bobot': item['bobot']} for item in jawaban_final}

    # Ambil file yang terkait dengan jawaban dalam satu query
    file_jawaban = FileJawaban.objects.filter(
        jawaban_id__in=jawaban_ids,
        deleted_at__isnull=True
    ).values('jawaban_id')

    # Buat set untuk memeriksa apakah ada file untuk jawaban
    file_jawaban_set = {item['jawaban_id'] for item in file_jawaban}

    # Iterasi setiap jawaban dan hitung total
    for item in jawaban:
        # Cek apakah jawaban_final ada untuk jawaban_id dan pilihan_id
        if (item['id'], item['pilihan_id']) in jawaban_final_set:
            jawaban_data = jawaban_final_set[(item['id'], item['pilihan_id'])]
            bobot = jawaban_data['bobot']
            
            # Periksa apakah statusnya 'diterima', dan jika ya, kalikan bobot dengan 1
            if jawaban_data['status'] == 'diterima':
                bobot *= 1
            else:
                bobot *= 0
            count_same += 1
        else:
            bobot = item['bobot']
            count_different += 1

        # Cek apakah text_jawaban ada dan tidak kosong, serta apakah ada file terkait
        if item['text_jawaban'] and item['text_jawaban'].strip() and item['id'] in file_jawaban_set:
            total_bobot += bobot  # Tambahkan bobot ke total_bobot jika ada jawaban dan file
        else:
            total_bobot = 0  # Jika tidak ada file atau text_jawaban kosong, set total_bobot menjadi 0

    return {
        'count_same': count_same,
        'count_different': count_different,
        'total_bobot': total_bobot
    }



# def count_answers(pertanyaan_instansi_id, pertanyaan_id, user_id, instansi_id, category):
#     # Ambil jawaban untuk user tertentu
#     if category == 'spesifik':
#         jawaban = (
#             Jawaban.objects
#             .filter(user_id=user_id, instansi_id=instansi_id, pertanyaan_instansi_id=pertanyaan_instansi_id, pertanyaan_id=pertanyaan_id, deleted_at__isnull=True)
#             .values('id','text_jawaban','pilihan_id','bobot')  # Ambil id dan pilihan_id
#         )
#     else:
#         jawaban = (
#             Jawaban.objects
#             .filter(user_id=user_id, instansi_id=instansi_id, pertanyaan_instansi_id=pertanyaan_instansi_id, pertanyaan_id=pertanyaan_id, deleted_at__isnull=True)
#             .values('id','text_jawaban','pilihan_id','bobot')  # Ambil id dan pilihan_id
#         )

#     # Inisialisasi hitungan
#     count_same = 0
#     count_different = 0
#     total_bobot = 0

#     # # Jika tidak ada jawaban, kembalikan 0
#     if not jawaban:
#         return {
#             'count_same': count_same,
#             'count_different': count_different,
#             'total_bobot': total_bobot
#         }

#     # Iterasi setiap jawaban
#     for item in jawaban:
#         # Cek jawaban final untuk pilihan_id dan id jawaban
#         jawaban_final = JawabanFinal.objects.filter(
#             jawaban_id=item['id'],
#             pilihan_id=item['pilihan_id'],
#             deleted_at__isnull=True
#         ).first()

#         # Hitung jawaban yang sama dan berbeda
#         if jawaban_final:
#             count_same += 1
#         else:
#             count_different += 1

        

#         if item['text_jawaban'] and item['text_jawaban'].strip():  # Mengecek apakah 'text_jawaban' tidak kosong dan tidak hanya spasi
#             total_bobot = item['bobot']
#         else:
#             total_bobot = 0

#     return {
#         'count_same': count_same,
#         'count_different': count_different,
#         'total_bobot': total_bobot
#     }


@csrf_exempt
def akumulasi_data(request):
    type = request.POST.get('type')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
    # current_year = timezone.now().year
    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms

    data = list(
        User.objects.exclude(deleted_at__isnull=False)
        .filter(role='operator')  # Filter berdasarkan role
        .values('id', 'instansi_id', 'instansi__name')  # Ambil id dan nama instansi
        .order_by('instansi__name')  # Urutkan berdasarkan nama instansi
    )

    form = Form.objects.filter(is_active=True)
    if form.exists():  # Check if there are any active forms
        current_year = form.first().year  # Get the year of the first active form
    else:
        current_year = None  # Handle the case where there are no active forms

    if type in ('semua', 'baku'):
        # Ambil jumlah pertanyaan baku
        baku = PertanyaanInstansi.objects.filter(
                form__year=current_year,
                category='baku',
                deleted_at__isnull=True
            )

    for index, item in enumerate(data):
        item['no'] = index + 1

        count_baku = 0
        count_spesifik = 0
        count_same = 0
        count_different = 0
        em = 0
        max = 0
        hitung_baku = {'count_same': 0, 'count_different': 0}
        hitung_spesifik = {'count_same': 0, 'count_different': 0}  # Inisialisasi di sini

        user_id = item['id']  # ID pengguna
        instansi_id = item['instansi_id']  # ID instansi

        # Ambil pertanyaan_id dan instansi_id untuk user yang relevan
        if type in ('semua', 'baku'):
            if baku.exists():  # Pastikan ada pertanyaan
                i=100
                for baku_instance in baku:  # Iterasi semua instance
                    pertanyaan_instansi_id = baku_instance.id  # Mengambil ID pertanyaan instansi
                    pertanyaan_id = baku_instance.pertanyaan_id  # Mengambil ID pertanyaan
                    category_baku = 'baku'  # Menggunakan kategori

                    # Mendapatkan pilihan berdasarkan pertanyaan_id
                    pilihan = Pilihan.objects.filter(pertanyaan_id=pertanyaan_id)

                    if pilihan.exists():
                        # Mencari pilihan dengan bobot terbesar
                        max_pilihan = pilihan.order_by('-bobot').first()  # Urutkan berdasarkan bobot, ambil yang pertama

                        if max_pilihan:
                            pilihan_id = max_pilihan.id  # Ambil pilihan_id
                            max = max + max_pilihan.bobot  # Ambil nilai bobot terbesar
                            print(f'Pilihan ID Baku: {pilihan_id}, Bobot: {max}')  # Debugging output
                        else:
                            print('Tidak ada pilihan tersedia untuk pertanyaan ini.')
                    else:
                        print('Tidak ada pilihan ditemukan untuk pertanyaan_id:', pertanyaan_id)

                    # Panggil fungsi hitung untuk masing-masing instance
                    hitung_baku = count_answers(pertanyaan_instansi_id, pertanyaan_id, user_id, instansi_id, category_baku)
                    count_same = count_same + hitung_baku['count_same']
                    count_different = count_different + hitung_baku['count_different']
                    em = em + hitung_baku['total_bobot']
                    i=i+1
                    print(i)  # Debugging: Cek hasil untuk setiap instance
                count_baku = baku.count()
        
        if type in ('semua', 'spesifik'):
            spesifik = PertanyaanInstansi.objects.filter(
                    instansi=item['instansi_id'],
                    form__year=current_year,
                    category='spesifik',
                    deleted_at__isnull=True
                )
            if spesifik.exists():
                j=200
                for spesifik_instance in spesifik:  # Iterasi semua instance
                    pertanyaan_instansi_id = spesifik_instance.id  # Mengambil ID pertanyaan instansi
                    pertanyaan_id = spesifik_instance.pertanyaan_id  # Mengambil ID pertanyaan
                    category_spesifik = 'spesifik'  # Menggunakan kategori

                    print(f"instansi {pertanyaan_instansi_id}")

                    # Mendapatkan pilihan berdasarkan pertanyaan_id
                    pilihan = Pilihan.objects.filter(pertanyaan_id=pertanyaan_id)

                    if pilihan.exists():
                        # Mencari pilihan dengan bobot terbesar
                        max_pilihan = pilihan.order_by('-bobot').first()  # Urutkan berdasarkan bobot, ambil yang pertama

                        if max_pilihan:
                            pilihan_id = max_pilihan.id  # Ambil pilihan_id
                            max = max + max_pilihan.bobot  # Ambil nilai bobot terbesar
                            print(f'Pilihan ID Spesifik: {pilihan_id}, Bobot: {max}')  # Debugging output
                        else:
                            print('Tidak ada pilihan tersedia untuk pertanyaan ini.')
                    else:
                        print('Tidak ada pilihan ditemukan untuk pertanyaan_id:', pertanyaan_id)

                    # Panggil fungsi hitung untuk masing-masing instance
                    hitung_spesifik = count_answers(pertanyaan_instansi_id, pertanyaan_id, user_id, instansi_id, category_spesifik)
                    count_same = count_same + hitung_spesifik['count_same']
                    count_different = count_different + hitung_spesifik['count_different']
                    em = em + hitung_spesifik['total_bobot']
                    j=j+1
                    print(j)
                count_spesifik = spesifik.count()

        total_count = count_baku + count_spesifik  # Total count dari baku dan spesifik
        print(f"item-{index}: {total_count}")
        if total_count > 0:  # Pastikan tidak pembagian dengan nol
            result = round(count_same / total_count, 2) * 100
        else:
            result = 0.0  # Penanganan lain jika perlu

        formatted_result = f"{result:.2f} %"  # Format hasil

        item['count'] = total_count
        item['valid'] = count_same  # Mengambil count_same
        item['invalid'] = count_different
        item['percentage'] = formatted_result  # Atur sesuai logika Anda
        item['em_value'] = em  # Atur sesuai logika Anda
        item['max_value'] = max  # Atur sesuai logika Anda

    return JsonResponse({'data': data})

def lihat_hasil(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        instansi = request.POST.get('instansi','').strip()
        instansi = escape(instansi)
        user = request.POST.get('user','').strip()
        user = escape(user)
        type = request.POST.get('type','').strip()
        type = escape(type)
        year = request.POST.get('yaer','').strip()
        year = escape(year)

        form = Form.objects.filter(is_active=True)
        if form.exists():  # Check if there are any active forms
            current_year = form.first().year  # Get the year of the first active form
        else:
            current_year = None  # Handle the case where there are no active forms

        query = PertanyaanInstansi.objects.filter(
                deleted_at__isnull=True
            )
        
        if type:
            # try:
            #     validate_category_pertanyaan(type)  # Pastikan instansi valid
            # except ValidationError as e:
            #     return JsonResponse({'success': False, 'message': str(e)})
            if(type != "semua"):
                query = query.filter(category=type)  # Asumsi instansi_id adalah field yang tepat
                if type == "spesifik":
                    # Tambahkan filter untuk instansi jika valid dan tidak kosong
                    if instansi:
                        try:
                            validate_id(instansi, Instansi)  # Pastikan instansi valid
                        except ValidationError as e:
                            return JsonResponse({'success': False, 'message': str(e)})
                        query = query.filter(instansi_id=instansi)  # Asumsi instansi_id adalah field yang tepat
                else:
                    query = query.filter(instansi_id__isnull=True)

        if year:
            try:
                validate_id(year,Form)  # Pastikan instansi valid
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            form = Form.objects.filter(is_active=True,id=year)
            if form.exists():  # Check if there are any active forms
                current_year = form.first().year  # Get the year of the first active form
            else:
                current_year = None  # Handle the case where there are no active forms
            query = query.filter(form__year=current_year)  # Asumsi instansi_id adalah field yang tepat
        else:
            # current_year = timezone.now().year
            query = query.filter(form__year=current_year)

        # Mendapatkan data berdasarkan kondisi instansi
        data_with_instansi = query.filter(instansi_id__isnull=False,instansi_id=instansi,deleted_at__isnull=True).values(
            'id',
            'pertanyaan_id',
            'pertanyaan_id__name',
            'pertanyaan_id__description',
            'pertanyaan_id__evaluation_note',
            'category',
            'instansi_id',
        )

        data_without_instansi = query.filter(instansi_id__isnull=True,deleted_at__isnull=True).values(
            'id',
            'pertanyaan_id',
            'pertanyaan_id__name',
            'pertanyaan_id__description',
            'pertanyaan_id__evaluation_note',
            'category',
        )

        print(data_with_instansi)
        print(data_without_instansi)

        # Menggabungkan hasil jika tidak kosong
        combined_data = []

        if data_with_instansi.exists():
            combined_data.extend(list(data_with_instansi))

        if data_without_instansi.exists():
            combined_data.extend(list(data_without_instansi))

        print(combined_data)

        data = query.values(  # Menggunakan .values() untuk mengambil field tertentu
            'id',
            'pertanyaan_id',
            'pertanyaan_id__name',
            'pertanyaan_id__description',
            'pertanyaan_id__evaluation_note',
            'category',
            'instansi_id',
        )
        
        # Mengonversi queryset ke list untuk manipulasi
        data = list(combined_data)

        getInstansi = Instansi.objects.filter(id=instansi).first()
        instansi_name = getInstansi.name

        max = 0
        for index, item in enumerate(data):
            # Mendapatkan pilihan berdasarkan pertanyaan_id
            pilihan = Pilihan.objects.filter(pertanyaan_id=item['pertanyaan_id'])

            if pilihan.exists():
                # Mencari pilihan dengan bobot terbesar
                max_pilihan = pilihan.order_by('-bobot').first()  # Urutkan berdasarkan bobot, ambil yang pertama

                if max_pilihan:
                    pilihan_id = max_pilihan.id  # Ambil pilihan_id
                    max =  max_pilihan.bobot  # Ambil nilai bobot terbesar
                    print(f'Pilihan ID Baku: {pilihan_id}, Bobot: {max}')  # Debugging output
                    item['max_value'] = max
                else:
                    item['max_value'] = 0
                    print('Tidak ada pilihan tersedia untuk pertanyaan ini.')
            else:
                item['max_value'] = 0
                print('Tidak ada pilihan ditemukan untuk pertanyaan_id:', item['pertanyaan_id'])
            
            # Mengambil jawaban terkait berdasarkan pertanyaan_instansi_id
            jawaban = Jawaban.objects.filter(
                deleted_at__isnull=True,
                pertanyaan_instansi_id=item['id'],
                user_id=user,
            ).values('id', 'text_jawaban','pilihan_id','bobot','pertanyaan_instansi_id','pertanyaan_id','user_id','instansi_id').first()  # Ambil jawaban pertama jika ada

            # Inisialisasi variabel
            item['jawaban'] = {}  # Inisialisasi jawaban
            item['file_jawaban'] = []  # Kosongkan default
            item['jawaban_final'] = {}  # Kosongkan default

            if jawaban:
                # Ambil semua file_jawaban terkait
                file_jawaban = FileJawaban.objects.filter(
                    deleted_at__isnull=True,
                    jawaban_id=jawaban['id'],
                    instansi_id=instansi,
                    user_id=user
                ).values('id', 'original_filename', 'encrypted_filename','user_id','instansi_id')

                # Ambil satu jawaban_final terkait
                jawaban_final = JawabanFinal.objects.filter(
                    deleted_at__isnull=True,
                    jawaban_id=jawaban['id'],
                    instansi_id=instansi,
                    user_id=user
                ).values('id', 'bobot', 'catatan', 'status', 'pilihan_id','user_id','instansi_id').first()

                # Mengonversi queryset ke list
                item['file_jawaban'] = list(file_jawaban)  # Mengonversi queryset ke list
                item['jawaban_final'] = jawaban_final if jawaban_final else {}  # Menetapkan jawaban_final

                # Mengatur jawaban ke dalam dictionary
                item['jawaban'] = {
                    'text_jawaban': jawaban['text_jawaban'],
                    'pilihan_id': jawaban['pilihan_id'],
                    'bobot': jawaban['bobot'],
                    'pertanyaan_instansi_id': jawaban['pertanyaan_instansi_id'],
                    'pertanyaan_id': jawaban['pertanyaan_id'],
                    'user_id': jawaban['user_id'],
                    'instansi_id': jawaban['instansi_id'],
                    'id': jawaban['id']
                }

            # Menambahkan informasi ke item
            item['no'] = index + 1
            item['instansi_id__name'] = instansi_name

        return JsonResponse({'data': data})


    return JsonResponse({'error': 'Invalid request'}, status=400)


# Instansi API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def instansi_data(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'select_one':
            query = request.POST.get('id', '')  # Get the search term
            results = []
            # Example: Assuming you have a model called Form
            if query:
                options = Instansi.objects.filter(id=query)  # Adjust field as needed
            else:
                options = Instansi.objects.all()  # Get all options if no query
            
            for option in options:
                results.append({
                    'id': option.id,
                    'text': option.name,  # Adjust based on your model's field
                })

            return JsonResponse({'results': results})
        if action == 'select':
            query = request.POST.get('q', '')  # Get the search term
            jawaban = request.POST.get('jawaban', '')  # Get the search term
            results = []

            if jawaban:
                print(jawaban)
                options = Jawaban.objects.filter(instansi__name__icontains=query).distinct('user_id')  # Adjust field as needed
                for option in options:
                    results.append({
                        'id': option.instansi.id,  # Mengambil ID dari instansi
                        'text': option.instansi.name,  # Mengambil nama dari instansi
                        'user': option.user.id,  # Mengambil ID pengguna
                    })
            else:
                # Example: Assuming you have a model called Form
                if query:
                    options = Instansi.objects.filter(name__icontains=query)  # Adjust field as needed
                    for option in options:
                        results.append({
                            'id': option.id,
                            'text': option.name,  # Adjust based on your model's field
                        })
                else:
                    options = Instansi.objects.all()  # Get all options if no query
                    for option in options:
                        results.append({
                            'id': option.id,
                            'text': option.name,  # Adjust based on your model's field
                        })


            # for option in options:
            #     results.append({
            #         'id': option.id,
            #         'text': option.name,  # Adjust based on your model's field
            #     })

            return JsonResponse({'results': results})
        if action == 'add':
            name = request.POST.get('name').strip()
            name = escape(name)
            try:
                validate_name(name)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            if Instansi.objects.filter(name=name).exists():
                return JsonResponse({'success': False, 'message': 'Nama Instansi sudah ada.'})
            new = Instansi.objects.create(name=name)
            return JsonResponse({'success': True})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = Instansi.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            name = request.POST.get('name').strip()
            id = escape(id)
            name = escape(name)
            try:
                validate_id(id,Instansi)
                validate_name(name)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})
            if Instansi.objects.filter(name=name).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Nama Instansi sudah ada.'})
            Instansi.objects.filter(id=id).update(name=name)
            return JsonResponse({'success': True})
    data = list(Instansi.objects.exclude(deleted_at__isnull=False).values('id', 'name').order_by('name'))
    for index, item in enumerate(data):
        item['no'] = index + 1
    return JsonResponse({'data': data})

# Master Pilihan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def masterpilihan_data(request):
    if request.method == 'GET':
        master_pilihan_id = request.GET.get('masterpilihan_id','').strip()
        master_pilihan_id = escape(master_pilihan_id)
        if master_pilihan_id:
            try:
                validate_id(master_pilihan_id,MasterPilihan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
    if request.method == 'POST':
        master_pilihan_id = request.GET.get('masterpilihan_id','').strip()
        master_pilihan_id = escape(master_pilihan_id)
        if master_pilihan_id:
            try:
                validate_id(master_pilihan_id,MasterPilihan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        action = request.POST.get('action')
        if action == 'select':
            query = request.POST.get('q', '')  # Get the search term
            results = []

            # Example: Assuming you have a model called MasterPilihan
            if query:
                options = MasterPilihan.objects.filter(name__icontains=query)  # Adjust field as needed
            else:
                options = MasterPilihan.objects.all()  # Get all options if no query

            for option in options:
                results.append({
                    'id': option.id,
                    'text': option.name,  # Adjust based on your model's field
                })

            return JsonResponse({'results': results})
        if action == 'add':
            name = request.POST.get('name','').strip()
            bobot = request.POST.get('bobot','').strip()
            name = escape(name)
            bobot = escape(bobot)
            try:
                validate_name(name)
                validate_double(bobot)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if MasterPilihan.objects.filter(name=name, bobot=bobot).exists():
                return JsonResponse({'success': False, 'message': 'Nama Master Pilihan sudah ada.'})

            new = MasterPilihan.objects.create(name=name,bobot=bobot)
            return JsonResponse({'success': True})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id, MasterPilihan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = MasterPilihan.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            name = request.POST.get('name').strip()
            bobot = request.POST.get('bobot').strip()
            id = escape(id)
            name = escape(name)
            bobot = escape(bobot)
            try:
                validate_id(id, MasterPilihan)
                validate_name(name)
                validate_double(bobot)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if MasterPilihan.objects.filter(name=name, bobot=bobot).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Master Pilihan sudah ada.'})
            
            MasterPilihan.objects.filter(id=id).update(name=name,bobot=bobot)
            return JsonResponse({'success': True})
        elif action == 'deactive':
            id = request.POST.get('id')
            active = request.POST.get('active') == 'true'
            MasterPilihan.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'active':
            id = request.POST.get('id')
            active = request.POST.get('active') == 'true'
            MasterPilihan.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
    # data = list(MasterPilihan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'bobot').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    if master_pilihan_id:
        # Filter directly on the queryset
        data = (
            MasterPilihan.objects
            .exclude(deleted_at__isnull=False)
            .filter(id=master_pilihan_id)
            .values('id', 'name','bobot')
            .order_by('id')
        )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    else:
        # Fetch all relevant records when no pertanyaan_id is provided
        data = (
            MasterPilihan.objects
            # .exclude(deleted_at__isnull=False)
            .values('id', 'name','bobot','deleted_at')
            .order_by('id')
        )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    if not data:
        return JsonResponse({'data': [], 'message': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'success':True,'data': data})

# Buku Panduan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def buku_panduan_data(request):        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            file_name = request.POST.get('name','').strip()
            version = request.POST.get('version','').strip()
            file_name = escape(file_name)
            version = escape(version)
            try:
                validate_name(file_name)
                # validate_name(evaluation_note)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if FileVersion.objects.filter(file_name=file_name, version=version, is_active=True).exists():
                return JsonResponse({'success': False, 'message': 'Nama Buku Panduan sudah ada.'})

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"

                    file_type = "manual"
                    
                    # Create a FileVersion instance for each uploaded file
                    file_instance = FileVersion(
                        file_name=file_name,
                        file=uploaded_file,
                        file_type=file_type,
                        version=version,
                        is_active=False,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = FileVersion.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'deactive':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            FileVersion.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'active':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            FileVersion.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            file_name = request.POST.get('name').strip()
            version = request.POST.get('version').strip()

            id = escape(id)
            file_name = escape(file_name)
            version = escape(version)

            try:
                validate_id(id, FileVersion)
                validate_name(file_name)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if FileVersion.objects.filter(file_name=file_name, version=version).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan sudah ada.'})
            
            # Update the Pertanyaan instance
            FileVersion.objects.filter(id=id).update(file_name=file_name, version=version)

            # Retrieve the Pertanyaan instance
            try:
                instance = FileVersion.objects.get(id=current_id)
            except FileVersion.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Pertanyaan not found.'})

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"

                    file_type = "manual"
                    
                    # Create a FileVersion instance for each uploaded file
                    
                    instance.file_name=file_name
                    instance.file=uploaded_file
                    instance.file_type=file_type
                    instance.version=version
                    # instance.is_active=True
                    instance.original_filename=original_filename
                    instance.encrypted_filename=new_filename  # Use the new filename
                    instance.file_extension=os.path.splitext(original_filename)[1]  # Extract file extension
                    instance.size=uploaded_file.size
                    instance.content_type=uploaded_file.content_type
                    
                    instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    # data = list(Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'type', 'description').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    # Initialize an empty queryset
    data = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="manual")

    # Select relevant fields and order the results
    data = data.values('id', 'file_name', 'version', 'is_active', 'encrypted_filename').order_by('id')

    # Convert the queryset to a list for enumeration
    data = list(data)

    # Enumerate to add 'no' to each item
    for index, item in enumerate(data):
        item['no'] = index + 1

    # Return the JSON response
    return JsonResponse({'success': True, 'data': data})

# Petunjuk Teknis API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def petunjuk_teknis_data(request):        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            file_name = request.POST.get('name','').strip()
            version = request.POST.get('version','').strip()
            file_name = escape(file_name)
            version = escape(version)
            try:
                validate_name(file_name)
                # validate_name(evaluation_note)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if FileVersion.objects.filter(file_name=file_name, version=version, is_active=True).exists():
                return JsonResponse({'success': False, 'message': 'Nama Buku Panduan sudah ada.'})

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"

                    file_type = "guide"
                    
                    # Create a FileVersion instance for each uploaded file
                    file_instance = FileVersion(
                        file_name=file_name,
                        file=uploaded_file,
                        file_type=file_type,
                        version=version,
                        is_active=False,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = FileVersion.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'deactive':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            FileVersion.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'active':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileVersion)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            FileVersion.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            file_name = request.POST.get('name').strip()
            version = request.POST.get('version').strip()

            id = escape(id)
            file_name = escape(file_name)
            version = escape(version)

            try:
                validate_id(id, FileVersion)
                validate_name(file_name)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if FileVersion.objects.filter(file_name=file_name, version=version).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan sudah ada.'})
            
            # Update the Pertanyaan instance
            FileVersion.objects.filter(id=id).update(file_name=file_name, version=version)

            # Retrieve the Pertanyaan instance
            try:
                instance = FileVersion.objects.get(id=current_id)
            except FileVersion.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Pertanyaan not found.'})

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"

                    file_type = "guide"
                    
                    # Create a FileVersion instance for each uploaded file
                    
                    instance.file_name=file_name
                    instance.file=uploaded_file
                    instance.file_type=file_type
                    instance.version=version
                    # instance.is_active=True
                    instance.original_filename=original_filename
                    instance.encrypted_filename=new_filename  # Use the new filename
                    instance.file_extension=os.path.splitext(original_filename)[1]  # Extract file extension
                    instance.size=uploaded_file.size
                    instance.content_type=uploaded_file.content_type
                    
                    instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    # data = list(Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'type', 'description').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    # Initialize an empty queryset
    data = FileVersion.objects.exclude(deleted_at__isnull=False).filter(file_type="guide")

    # Select relevant fields and order the results
    data = data.values('id', 'file_name', 'version', 'is_active', 'encrypted_filename').order_by('id')

    # Convert the queryset to a list for enumeration
    data = list(data)

    # Enumerate to add 'no' to each item
    for index, item in enumerate(data):
        item['no'] = index + 1

    # Return the JSON response
    return JsonResponse({'success': True, 'data': data})

# Pertanyaan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def pertanyaan_data(request):
    if request.method == 'GET':
        pertanyaan_id = request.GET.get('pertanyaan_id','').strip()
        pertanyaan_id = escape(pertanyaan_id)
        type_pertanyaan = request.GET.get('type_pertanyaan','').strip()
        type_pertanyaan = escape(type_pertanyaan)
        category_pertanyaan = request.GET.get('category_pertanyaan','').strip()
        category_pertanyaan = escape(category_pertanyaan)
        if pertanyaan_id or type_pertanyaan or category_pertanyaan:
            if pertanyaan_id:
                try:
                    validate_id(pertanyaan_id,Pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if type_pertanyaan:  # Only validate if type_pertanyaan is provided
                try:
                    validate_type_pertanyaan(type_pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if category_pertanyaan:  # Only validate if category_pertanyaan is provided
                try:
                    validate_category_pertanyaan(category_pertanyaan)  # Adjust validation function if necessary
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
                
    if request.method == 'POST':
        pertanyaan_id = request.GET.get('pertanyaan_id','').strip()
        pertanyaan_id = escape(pertanyaan_id)
        type_pertanyaan = request.GET.get('type_pertanyaan','').strip()
        type_pertanyaan = escape(type_pertanyaan)
        category_pertanyaan = request.GET.get('category_pertanyaan','').strip()
        category_pertanyaan = escape(category_pertanyaan)
        if pertanyaan_id or type_pertanyaan or category_pertanyaan:
            if pertanyaan_id:
                try:
                    validate_id(pertanyaan_id,Pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if type_pertanyaan:  # Only validate if type_pertanyaan is provided
                try:
                    validate_type_pertanyaan(type_pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if category_pertanyaan:  # Only validate if category_pertanyaan is provided
                try:
                    validate_category_pertanyaan(category_pertanyaan)  # Adjust validation function if necessary
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

        action = request.POST.get('action')
        if action == 'select':
            query = request.POST.get('q', '')  # Get the search term
            results = []

            # Example: Assuming you have a model called Form
            if query:
                options = Pertanyaan.objects.filter(name__icontains=query, category=category_pertanyaan, deleted_at__isnull=True)
            else:
                options = Pertanyaan.objects.filter(deleted_at__isnull=True, category=category_pertanyaan)  # Get all options if no query


            for option in options:
                results.append({
                    'id': option.id,
                    'text': option.name,  # Adjust based on your model's field
                })

            return JsonResponse({'results': results})
        if action == 'add':
            name = request.POST.get('name','').strip()
            type = request.POST.get('type','').strip()
            category = request.POST.get('category','').strip()
            description = request.POST.get('description','').strip()
            evaluation_note = request.POST.get('evaluation_note','').strip()
            name = escape(name)
            type = escape(type)
            category = escape(category)
            description = escape(description)
            evaluation_note = escape(evaluation_note)
            try:
                validate_name(name)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_name(description)
                # validate_name(evaluation_note)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if Pertanyaan.objects.filter(name=name, type=type, category=category, description=description).exists():
                return JsonResponse({'success': False, 'message': 'Nama Pertanyaan sudah ada.'})

            new = Pertanyaan.objects.create(name=name, type=type, category=category, description=description, evaluation_note=evaluation_note)

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaan(
                        pertanyaan=new,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = Pertanyaan.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            name = request.POST.get('name').strip()
            type = request.POST.get('type').strip()
            category = request.POST.get('category').strip()
            description = request.POST.get('description').strip()
            evaluation_note = request.POST.get('evaluation_note').strip()

            id = escape(id)
            name = escape(name)
            type = escape(type)
            category = escape(category)
            description = escape(description)
            evaluation_note = escape(evaluation_note)

            try:
                validate_id(id, Pertanyaan)
                validate_name(name)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_name(description)
                # validate_name(evaluation_note)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if Pertanyaan.objects.filter(name=name, type=type, category=category, description=description, evaluation_note=evaluation_note).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan sudah ada.'})
            
            # Update the Pertanyaan instance
            Pertanyaan.objects.filter(id=id).update(name=name, type=type, category=category, description=description)

            # Retrieve the Pertanyaan instance
            try:
                pertanyaan_instance = Pertanyaan.objects.get(id=current_id)
            except Pertanyaan.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Pertanyaan not found.'})

                        # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaan(
                        pertanyaan=pertanyaan_instance,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    # data = list(Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'type', 'description').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    # Initialize an empty queryset
    if category_pertanyaan:
        data = Pertanyaan.objects.exclude(deleted_at__isnull=False).filter(category=category_pertanyaan)
    else:
        data = Pertanyaan.objects.exclude(deleted_at__isnull=False)

    # If pertanyaan_id is provided, filter by it
    if pertanyaan_id:
        data = data.filter(id=pertanyaan_id)
    else:
        # If no pertanyaan_id, apply further filtering based on category
        if category_pertanyaan:
            # Start with the filter to exclude deleted items
            filters = {'deleted_at__isnull': True}  # Ensure only non-deleted items

            # Define allowed types for filtering
            allowed_types = ['multiple', 'checkbox', 'likert', 'multi-select', 'rating']
            
            # Add type filter to filters
            filters['type__in'] = allowed_types  # Include allowed types

            # Add category filter if provided
            filters['category'] = category_pertanyaan

            # Apply the filters to the queryset
            data = data.filter(**filters)

    # Select relevant fields and order the results
    data = data.values('id', 'name', 'type', 'category', 'description', 'evaluation_note').order_by('id')

    # Convert the queryset to a list for enumeration
    data = list(data)

    # Enumerate to add 'no' to each item
    for index, item in enumerate(data):
        item['no'] = index + 1

    # Return the JSON response
    return JsonResponse({'success': True, 'data': data})


# File Pertanyaan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def filepertanyaan_data(request):
    if request.method == 'POST':        
        pertanyaan_id = request.GET.get('pertanyaan_id','').strip()
        pertanyaan_id = escape(pertanyaan_id)
        if pertanyaan_id:
            try:
                validate_id(pertanyaan_id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        action = request.POST.get('action')
        if action == 'add':
            file = request.POST.get('file')

            # if FilePertanyaan.objects.filter(file=file).exists():
            #     return JsonResponse({'success': False, 'message': 'Nama Form sudah ada.'})

            # new = FilePertanyaan.objects.create(file=file)

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaan(
                        pertanyaan=pertanyaan_id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FilePertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = FilePertanyaan.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            file = request.POST.get('file')

            id = escape(id)
            try:
                validate_id(id,FilePertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if FilePertanyaan.objects.filter(file=file).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'File Pertanyaan sudah ada.'})
            
            FilePertanyaan.objects.filter(id=id).update(file=file)
            return JsonResponse({'success': True})
    if pertanyaan_id:
        # Filter directly on the queryset
        data = (
            FilePertanyaan.objects
            .exclude(deleted_at__isnull=False)
            .filter(pertanyaan_id=pertanyaan_id)
            .values('id', 'original_filename','encrypted_filename')
            .order_by('id')
        )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    else:
        # Fetch all relevant records when no pertanyaan_id is provided
        data = (
            FilePertanyaan.objects
            .exclude(deleted_at__isnull=False)
            .values('id', 'original_filename','encrypted_filename')
            .order_by('id')
        )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    return JsonResponse({'data': data})

# File Pertanyaan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def filepertanyaaninstansi_data(request):
    if request.method == 'POST':        
        pertanyaan_instansi_id = request.GET.get('pertanyaan_instansi_id','').strip()
        pertanyaan_instansi_id = escape(pertanyaan_instansi_id)
        if pertanyaan_instansi_id:
            try:
                validate_id(pertanyaan_instansi_id,PertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        action = request.POST.get('action')
        if action == 'add':
            file = request.POST.get('file')

            # if FilePertanyaan.objects.filter(file=file).exists():
            #     return JsonResponse({'success': False, 'message': 'Nama Form sudah ada.'})

            # new = FilePertanyaan.objects.create(file=file)

                        # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaanInstansi(
                        pertanyaan_instansi_id=pertanyaan_instansi_id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FilePertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = FilePertanyaanInstansi.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            file = request.POST.get('file')

            id = escape(id)
            try:
                validate_id(id,FilePertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if FilePertanyaanInstansi.objects.filter(file=file).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'File Pertanyaan Instansi sudah ada.'})
            
            FilePertanyaanInstansi.objects.filter(id=id).update(file=file)
            return JsonResponse({'success': True})
        if pertanyaan_instansi_id:
            # Filter directly on the queryset
            data = (
                FilePertanyaanInstansi.objects
                .exclude(deleted_at__isnull=False)
                .filter(pertanyaan_instansi_id=pertanyaan_instansi_id)
                .values('id', 'original_filename','encrypted_filename')
                .order_by('id')
            )

            # Enumerate to add 'no' to each item
            data = list(data)  # Convert to list for enumeration
            for index, item in enumerate(data):
                item['no'] = index + 1
        else:
            # Fetch all relevant records when no pertanyaan_id is provided
            data = (
                FilePertanyaanInstansi.objects
                .exclude(deleted_at__isnull=False)
                .values('id', 'original_filename','encrypted_filename')
                .order_by('id')
            )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    return JsonResponse({'data': data})

# File Pertanyaan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def filejawaban_data(request):
    if request.method == 'POST':        
        jawaban = request.GET.get('jawaban','').strip()
        jawaban = escape(jawaban)
        if jawaban:
            try:
                validate_id(jawaban,Jawaban)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        action = request.POST.get('action')
        if action == 'add':
            file = request.POST.get('file')

            # if FilePertanyaan.objects.filter(file=file).exists():
            #     return JsonResponse({'success': False, 'message': 'Nama Form sudah ada.'})

            # new = FilePertanyaan.objects.create(file=file)
        
            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FileJawaban(
                        user=request.user.id,
                        instansi=request.user.instansi_id,
                        jawaban=jawaban,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,FileJawaban)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = FileJawaban.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            file = request.POST.get('file')

            id = escape(id)
            try:
                validate_id(id,FilePertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if FilePertanyaanInstansi.objects.filter(file=file).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'File Pertanyaan Instansi sudah ada.'})
            
            FilePertanyaanInstansi.objects.filter(id=id).update(file=file)
            return JsonResponse({'success': True})
        if jawaban:
            # Filter directly on the queryset
            data = (
                FileJawaban.objects
                .exclude(deleted_at__isnull=False)
                .filter(jawaban=jawaban)
                .values('id', 'original_filename','encrypted_filename')
                .order_by('id')
            )

            # Enumerate to add 'no' to each item
            data = list(data)  # Convert to list for enumeration
            for index, item in enumerate(data):
                item['no'] = index + 1
        else:
            # Fetch all relevant records when no pertanyaan_id is provided
            data = (
                FileJawaban.objects
                .exclude(deleted_at__isnull=False)
                .values('id', 'original_filename','encrypted_filename')
                .order_by('id')
            )

        # Enumerate to add 'no' to each item
        data = list(data)  # Convert to list for enumeration
        for index, item in enumerate(data):
            item['no'] = index + 1
    return JsonResponse({'data': data})

# Pilihan API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def pilihan_data(request):
    if request.method == 'GET':
        pertanyaan_id = request.GET.get('pertanyaan_id','').strip()
        pertanyaan_id = escape(pertanyaan_id)
        if pertanyaan_id:
            try:
                validate_id(pertanyaan_id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
    if request.method == 'POST':
        pertanyaan_id = request.GET.get('pertanyaan_id','').strip()
        pertanyaan_id = escape(pertanyaan_id)
        if pertanyaan_id:
            try:
                validate_id(pertanyaan_id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        action = request.POST.get('action')
        if action == 'add':
            bobot = request.POST.get('bobot','').strip()
            order = request.POST.get('order','').strip()
            master_pilihan_id = request.POST.get('pilihan','').strip()
            pertanyaan_id = request.POST.get('pertanyaan','').strip()

            bobot = escape(bobot)
            order = escape(order)
            master_pilihan_id = escape(master_pilihan_id)
            pertanyaan_id = escape(pertanyaan_id)

            try:
                validate_double(bobot)
                validate_id(master_pilihan_id,MasterPilihan)
                validate_id(pertanyaan_id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                # Check if MasterPilihan with the given name and bobot exists
                master_pilihan = MasterPilihan.objects.filter(id=master_pilihan_id, bobot=bobot).first()

                if not master_pilihan:
                    get = MasterPilihan.objects.filter(id=master_pilihan_id).first()

                    # If it doesn't exist, create a new one
                    master_pilihan = MasterPilihan.objects.create(
                        name=get.name,  # Assuming 'name' is the same as 'bobot' in this context
                        bobot=bobot
                    )

                    master_pilihan_id = master_pilihan.id

                # Check for existing Pilihan
                if Pilihan.objects.filter(
                    bobot=bobot,
                    order=order,
                    master_pilihan_id=master_pilihan_id,
                    pertanyaan_id=pertanyaan_id
                ).exists():
                    return JsonResponse({'success': False, 'message': 'Pilihan Pertanyaan sudah ada.'})

                # Create new Pilihan
                new_pilihan = Pilihan.objects.create(
                    bobot=bobot,
                    order=order,
                    master_pilihan_id=master_pilihan_id,
                    pertanyaan_id=pertanyaan_id
                )
                return JsonResponse({'success': True, 'message': 'Pilihan baru telah ditambahkan.'})

            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})


        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Pilihan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = Pilihan.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id','').strip()
            bobot = request.POST.get('bobot','').strip()
            order = request.POST.get('order','').strip()
            master_pilihan_id = request.POST.get('pilihan','').strip()
            pertanyaan_id = request.POST.get('pertanyaan','').strip()

            id = escape(id)
            bobot = escape(bobot)
            order = escape(order)
            master_pilihan_id = escape(master_pilihan_id)
            pertanyaan_id = escape(pertanyaan_id)

            try:
                validate_double(bobot)
                validate_id(master_pilihan_id,MasterPilihan)
                validate_id(pertanyaan_id,Pertanyaan)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if Pilihan.objects.filter(bobot=bobot, order=order, master_pilihan_id=master_pilihan_id, pertanyaan_id=pertanyaan_id).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Nama Pilihan sudah ada.'})
            
            Pilihan.objects.filter(id=id).update(bobot=bobot, order=order, master_pilihan_id=master_pilihan_id, pertanyaan_id=pertanyaan_id)
            return JsonResponse({'success': True})
    if pertanyaan_id:
        data = list(Pilihan.objects.exclude(deleted_at__isnull=False).filter(pertanyaan_id=pertanyaan_id).values('id', 'bobot', 'order', 'master_pilihan_id__name', 'pertanyaan__name', 'master_pilihan_id', 'pertanyaan_id', 'pertanyaan__type', 'pertanyaan__category').order_by('pertanyaan_id', 'master_pilihan_id'))
    else:
        data = list(Pilihan.objects.exclude(deleted_at__isnull=False).values('id', 'bobot', 'order', 'master_pilihan_id__name','pertanyaan__name','master_pilihan_id','pertanyaan_id','pertanyaan__type','pertanyaan__category').order_by('pertanyaan_id','master_pilihan_id'))
    for index, item in enumerate(data):
        item['no'] = index + 1
    return JsonResponse({'success': True,'data': data})

# Form API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def form_data(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'select':
            query = request.POST.get('q', '')  # Get the search term
            results = []

            # Example: Assuming you have a model called Form
            if query:
                options = Form.objects.filter(name__icontains=query)  # Adjust field as needed
            else:
                options = Form.objects.all()  # Get all options if no query

            for option in options:
                results.append({
                    'id': option.id,
                    'text': option.name,  # Adjust based on your model's field
                })

            return JsonResponse({'results': results})
        if action == 'add':
            name = request.POST.get('name').strip()
            year = request.POST.get('year').strip()
            startdate = request.POST.get('startdate').strip()
            starttime = request.POST.get('starttime').strip()
            enddate = request.POST.get('enddate').strip()
            endtime = request.POST.get('endtime').strip()

            name = escape(name)
            year = escape(year)
            startdate = escape(startdate)
            starttime = escape(starttime)
            enddate = escape(enddate)
            endtime = escape(endtime)

            try:
                validate_name(name)
                validate_year(year)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            start_datetime_str = f"{startdate} {starttime}"
            end_datetime_str = f"{enddate} {endtime}"

            try:
                # Adjusting the format to match the actual data
                start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Format tanggal atau waktu tidak valid.'})

            if Form.objects.filter(name=name, year=year).exists():
                return JsonResponse({'success': False, 'message': 'Nama Form sudah ada.'})

            new = Form.objects.create(name=name, year=year, start=start_datetime, end=end_datetime, is_active=True)
            return JsonResponse({'success': True})
        if action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Form)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = Form.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            name = request.POST.get('name').strip()
            year = request.POST.get('year').strip()
            startdate = request.POST.get('startdate').strip()
            starttime = request.POST.get('starttime').strip()
            enddate = request.POST.get('enddate').strip()
            endtime = request.POST.get('endtime').strip()

            id = escape(id)
            name = escape(name)
            year = escape(year)
            startdate = escape(startdate)
            starttime = escape(starttime)
            enddate = escape(enddate)
            starttime = escape(starttime)

            try:
                validate_id(id,Form)
                validate_name(name)
                validate_year(year)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            start_datetime_str = f"{startdate} {starttime}"
            end_datetime_str = f"{enddate} {endtime}"

            try:
                # Adjusting the format to match the actual data
                start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Format tanggal atau waktu tidak valid.'})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if Form.objects.filter(name=name, year=year).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Nama Form sudah ada.'})
            
            Form.objects.filter(id=id).update(name=name,year=year,start=start_datetime,end=end_datetime)
            return JsonResponse({'success': True})
        elif action == 'deactive':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Form)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            Form.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
        elif action == 'active':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,Form)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            active = request.POST.get('active') == 'true'
            Form.objects.filter(id=id).update(is_active=active)
            return JsonResponse({'success': True})
    data = list(Form.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'year', 'start','end', 'is_active').order_by('name'))
    for index, item in enumerate(data):
        item['no'] = index + 1
    return JsonResponse({'data': data})

# @csrf_exempt
def tahun_data(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'select':
            query = request.POST.get('q', '')  # Get the search term
            results = []

            # Example: Assuming you have a model called Form
            if query:
                options = Form.objects.filter(name__icontains=query)  # Adjust field as needed
            else:
                options = Form.objects.all()  # Get all options if no query

            for option in options:
                results.append({
                    'id': option.id,
                    'text': option.year,  # Adjust based on your model's field
                })

            return JsonResponse({'results': results})

# Pertanyaan Baku API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def pertanyaan_baku_data(request):
    category_pertanyaan = request.GET.get('category_pertanyaan_baku','').strip()
    category_pertanyaan = escape(category_pertanyaan)
    if request.method == 'POST':
        pertanyaan = request.GET.get('pertanyaan_baku','').strip()
        pertanyaan = escape(pertanyaan)
        type_pertanyaan = request.GET.get('type_pertanyaan_baku','').strip()
        type_pertanyaan = escape(type_pertanyaan)
        form_pertanyaan = request.GET.get('form_pertanyaan_baku','').strip()
        form_pertanyaan = escape(form_pertanyaan)
        instansi_pertanyaan = request.GET.get('instansi_pertanyaan_baku','').strip()
        instansi_pertanyaan = escape(instansi_pertanyaan)
        instansi_pertanyaan = None
        if pertanyaan or type_pertanyaan or category_pertanyaan or category_pertanyaan or form_pertanyaan or instansi_pertanyaan:
            if pertanyaan:  # Only validate if pertanyaan is provided
                try:
                    validate_id(pertanyaan,Pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
                
            if type_pertanyaan:  # Only validate if type_pertanyaan is provided
                try:
                    validate_type_pertanyaan(type_pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if category_pertanyaan:  # Only validate if category_pertanyaan is provided
                try:
                    validate_category_pertanyaan(category_pertanyaan)  # Adjust validation function if necessary
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
            
            if form_pertanyaan:  # Only validate if form is provided
                try:
                    validate_id(form_pertanyaan,Form)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
                
            # if instansi_pertanyaan:  # Only validate if instansi is provided
            #     try:
            #         validate_id(instansi_pertanyaan,Instansi)
            #     except ValidationError as e:
            #         return JsonResponse({'success': False, 'message': str(e)})

        action = request.POST.get('action')
        if action == 'count':
            filters = {'deleted_at__isnull': True}
            filters["form_id"] = form_pertanyaan
            filters["instansi_id"] = instansi_pertanyaan
            filters["category"] = 'baku'
            data = (PertanyaanInstansi.objects
                    .filter(**filters)
                    .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
                    .order_by('form__name', 'instansi__name', 'order')
                    )
            
            last_entry = data.last()  # Get the last entry
            
            if last_entry is not None:
                last_entry['no'] = 1  # Assign 'no' as 1 since it's the only entry
                return JsonResponse({'success': True, 'message': 'success', 'data': last_entry})
            else:
                return JsonResponse({'success': False, 'message': 'No entries found.'})
        elif action == 'add':
            pertanyaan = request.POST.get('pertanyaan','').strip()
            type = request.POST.get('type','').strip()
            category = request.POST.get('category','').strip()
            form = request.POST.get('form','').strip()
            # instansi = request.POST.get('instansi','').strip()
            instansi = None
            order = request.POST.get('order','').strip()
            pertanyaan = escape(pertanyaan)
            type = escape(type)
            category = escape(category)
            form = escape(form)
            # instansi = escape(instansi)
            order = escape(order)
            try:
                validate_id(pertanyaan,Pertanyaan)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_id(form,Form)
                # validate_id(instansi,Instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if PertanyaanInstansi.objects.filter(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, deleted_at__isnull=True).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan Baku sudah ada.'})

            new = PertanyaanInstansi.objects.create(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, order=order)

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaanInstansi(
                        pertanyaan_instansi_id=new.id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        elif action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,PertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = PertanyaanInstansi.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            pertanyaan = request.POST.get('pertanyaan','').strip()
            type = request.POST.get('type','').strip()
            category = request.POST.get('category','').strip()
            form = request.POST.get('form','').strip()
            # instansi = request.POST.get('instansi','').strip()
            instansi = None
            order = request.POST.get('order','').strip()

            id = escape(id)
            pertanyaan = escape(pertanyaan)
            type = escape(type)
            category = escape(category)
            form = escape(form)
            # instansi = escape(instansi)
            order = escape(order)

            try:
                validate_id(id,PertanyaanInstansi)
                validate_id(pertanyaan,Pertanyaan)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_id(form,Form)
                # validate_id(instansi,Instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if PertanyaanInstansi.objects.filter(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan Baku sudah ada.'})
            
            PertanyaanInstansi.objects.filter(id=id).update(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, order=order)
        
            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaanInstansi(
                        pertanyaan_instansi_id=id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    # data = list(Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'type', 'description').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    if category_pertanyaan:
        filters = {'deleted_at__isnull': True}  # Start with the filter to exclude deleted items

        # Define allowed types for filtering
        allowed_types = ['multiple', 'checkbox', 'likert', 'multi-select', 'rating']
        
        # Add type filter to filters
        filters['type__in'] = allowed_types  # Always include allowed types

        # Add category filter if provided
        filters['category'] = 'baku'

        # Filter directly on the queryset
        data = (
            PertanyaanInstansi.objects
            .filter(**filters)
            .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
            .order_by('id','form__name','instansi__name','order')
        )
    else:
        # Fetch all relevant records when no category filter is provided
        data = (
            PertanyaanInstansi.objects
            .exclude(deleted_at__isnull=False).filter(category='baku')
            .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
            .order_by('form__name','instansi__name','order')
        )

    # Enumerate to add 'no' to each item
    data = list(data)  # Convert to list for enumeration
    for index, item in enumerate(data):
        item['no'] = index + 1

    return JsonResponse({'success': True, 'data': data})

# Pertanyaan Spesifik API
# @method_decorator(login_required, name='dispatch')
# @method_decorator(user_passes_test(is_admin), name='dispatch')
@csrf_exempt
@login_required
# @user_passes_test(is_admin)
def pertanyaan_spesifik_data(request):
    category_pertanyaan = request.GET.get('category_pertanyaan_spesifik','').strip()
    category_pertanyaan = escape(category_pertanyaan)
    if request.method == 'POST':
        pertanyaan = request.GET.get('pertanyaan_spesifik','').strip()
        pertanyaan = escape(pertanyaan)
        type_pertanyaan = request.GET.get('type_pertanyaan_spesifik','').strip()
        type_pertanyaan = escape(type_pertanyaan)
        form_pertanyaan = request.GET.get('form_pertanyaan_spesifik','').strip()
        form_pertanyaan = escape(form_pertanyaan)
        instansi_pertanyaan = request.GET.get('instansi_pertanyaan_spesifik','').strip()
        instansi_pertanyaan = escape(instansi_pertanyaan)
        if pertanyaan or type_pertanyaan or category_pertanyaan or category_pertanyaan or form_pertanyaan or instansi_pertanyaan:
            if pertanyaan:  # Only validate if pertanyaan is provided
                try:
                    validate_id(pertanyaan,Pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
                
            if type_pertanyaan:  # Only validate if type_pertanyaan is provided
                try:
                    validate_type_pertanyaan(type_pertanyaan)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

            if category_pertanyaan:  # Only validate if category_pertanyaan is provided
                try:
                    validate_category_pertanyaan(category_pertanyaan)  # Adjust validation function if necessary
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
            
            if form_pertanyaan:  # Only validate if form is provided
                try:
                    validate_id(form_pertanyaan,Form)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})
                
            if instansi_pertanyaan:  # Only validate if instansi is provided
                try:
                    validate_id(instansi_pertanyaan,Instansi)
                except ValidationError as e:
                    return JsonResponse({'success': False, 'message': str(e)})

        action = request.POST.get('action')
        if action == 'count':
            filters = {'deleted_at__isnull': True}
            filters["form_id"] = form_pertanyaan
            filters["instansi_id"] = instansi_pertanyaan
            filters["category"] = 'spesifik'
            data = (PertanyaanInstansi.objects
                    .filter(**filters)
                    .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
                    .order_by('form__name', 'instansi__name', 'order')
                    )
            
            last_entry = data.last()  # Get the last entry
            
            if last_entry is not None:
                last_entry['no'] = 1  # Assign 'no' as 1 since it's the only entry
                return JsonResponse({'success': True, 'message': 'success', 'data': last_entry})
            else:
                return JsonResponse({'success': False, 'message': 'No entries found.'})
        elif action == 'add':
            pertanyaan = request.POST.get('pertanyaan','').strip()
            type = request.POST.get('type','').strip()
            category = request.POST.get('category','').strip()
            form = request.POST.get('form','').strip()
            instansi = request.POST.get('instansi','').strip()
            order = request.POST.get('order','').strip()
            pertanyaan = escape(pertanyaan)
            type = escape(type)
            category = escape(category)
            form = escape(form)
            instansi = escape(instansi)
            order = escape(order)

            print("pertanyaan "+pertanyaan)
            print("type "+type)
            print("category "+category)
            print("form "+form)
            print("instansi "+instansi)
            print("order "+order)
            try:
                validate_id(pertanyaan,Pertanyaan)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_id(form,Form)
                validate_id(instansi,Instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})

            if PertanyaanInstansi.objects.filter(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, deleted_at__isnull=True).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan Spesifik sudah ada.'})

            new = PertanyaanInstansi.objects.create(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, order=order)

            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaanInstansi(
                        pertanyaan_instansi_id=new.id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        elif action == 'delete':
            id = request.POST.get('id').strip()
            id = escape(id)
            try:
                validate_id(id,PertanyaanInstansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            delete = PertanyaanInstansi.objects.filter(id=id).first()
            if delete:
                delete.deleted_at = timezone.now()
                delete.save()
                return JsonResponse({'success': True})
        elif action == 'edit':
            id = request.POST.get('id').strip()
            pertanyaan = request.POST.get('pertanyaan','').strip()
            type = request.POST.get('type','').strip()
            category = request.POST.get('category','').strip()
            form = request.POST.get('form','').strip()
            instansi = request.POST.get('instansi','').strip()
            order = request.POST.get('order','').strip()

            id = escape(id)
            pertanyaan = escape(pertanyaan)
            type = escape(type)
            category = escape(category)
            form = escape(form)
            instansi = escape(instansi)
            order = escape(order)

            try:
                validate_id(id,PertanyaanInstansi)
                validate_id(pertanyaan,Pertanyaan)
                validate_type_pertanyaan(type)
                validate_category_pertanyaan(category)
                validate_id(form,Form)
                validate_id(instansi,Instansi)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)})
            
            try:
                current_id = int(id)  # Convert to integer if necessary
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid ID format.'})

            if PertanyaanInstansi.objects.filter(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi).exclude(id=current_id).exists():
                return JsonResponse({'success': False, 'message': 'Pertanyaan Spesifik sudah ada.'})
            
            PertanyaanInstansi.objects.filter(id=id).update(pertanyaan_id=pertanyaan, type=type, category=category, form_id=form, instansi_id=instansi, order=order)

            print(request.FILES)  # Check what files are being received
            
            # Handle file uploads
            uploaded_files = request.FILES.getlist('files[]')  # Use getlist to handle multiple files
            # Validasi jumlah maksimum file
            max_files = 5
            if len(uploaded_files) > max_files:
                return JsonResponse({'success': False, 'error': f'Jumlah file tidak boleh lebih dari {max_files}.'})

            # Validasi setiap file yang di-upload
            max_filename_length = 255
            # max_content_type_length = 50
            max_file_extension_length = 10

            for uploaded_file in uploaded_files:
                original_filename = uploaded_file.name
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(original_filename)[1]

                # Validasi panjang nama file
                if len(original_filename) > max_filename_length:
                    return JsonResponse({'success': False, 'error': f'Nama file "{original_filename}" terlalu panjang. Maksimal {max_filename_length} karakter.'})
                
                # Validasi panjang content_type
                # if len(content_type) > max_content_type_length:
                #     return JsonResponse({'success': False, 'error': f'Content type "{content_type}" terlalu panjang. Maksimal {max_content_type_length} karakter.'})
                
                # Validasi panjang file_extension
                if len(file_extension) > max_file_extension_length:
                    return JsonResponse({'success': False, 'error': f'File extension "{file_extension}" terlalu panjang. Maksimal {max_file_extension_length} karakter.'})

            try:
                for uploaded_file in uploaded_files:
                    # Generate a new unique filename using a timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
                    original_filename = uploaded_file.name

                    unique_id = str(uuid.uuid4())
                    
                    # Create a new filename using the timestamp
                    new_filename = f"{unique_id}{os.path.splitext(original_filename)[1]}"
                    
                    # Create a FilePertanyaan instance for each uploaded file
                    file_instance = FilePertanyaanInstansi(
                        pertanyaan_instansi_id=id,
                        file=uploaded_file,
                        original_filename=original_filename,
                        encrypted_filename=new_filename,  # Use the new filename
                        file_extension=os.path.splitext(original_filename)[1],  # Extract file extension
                        size=uploaded_file.size,
                        content_type=uploaded_file.content_type,
                    )
                    file_instance.save()  # Save the instance to the database
                return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    # data = list(Pertanyaan.objects.exclude(deleted_at__isnull=False).values('id', 'name', 'type', 'description').order_by('name'))
    # for index, item in enumerate(data):
    #     item['no'] = index + 1
    if category_pertanyaan:
        filters = {'deleted_at__isnull': True}  # Start with the filter to exclude deleted items

        # Define allowed types for filtering
        allowed_types = ['multiple', 'checkbox', 'likert', 'multi-select', 'rating']
        
        # Add type filter to filters
        filters['type__in'] = allowed_types  # Always include allowed types

        # Add category filter if provided
        filters['category'] = 'spesifik'

        # Filter directly on the queryset
        data = (
            PertanyaanInstansi.objects
            .filter(**filters)
            .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
            .order_by('id','form__name','instansi__name','order')
        )
    else:
        # Fetch all relevant records when no category filter is provided
        data = (
            PertanyaanInstansi.objects
            .exclude(deleted_at__isnull=False).filter(category='spesifik')
            .values('id', 'form', 'form__name', 'form__year', 'instansi', 'instansi__name', 'order', 'pertanyaan', 'pertanyaan__name', 'type', 'category')
            .order_by('form__name','instansi__name','order')
        )

    # Enumerate to add 'no' to each item
    data = list(data)  # Convert to list for enumeration
    for index, item in enumerate(data):
        item['no'] = index + 1

    return JsonResponse({'success': True, 'data': data})

# User Views
class UserListView(View):
    def get(self, request):
        users = User.objects.all()
        return render(request, 'user_list.html', {'users': users})

class UserCreateView(View):
    def get(self, request):
        form = UserForm()
        return render(request, 'user_form.html', {'form': form})

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
        return render(request, 'user_form.html', {'form': form})

class UserUpdateView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserForm(instance=user)
        return render(request, 'user_form.html', {'form': form})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
        return render(request, 'user_form.html', {'form': form})

class UserDeleteView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, 'user_confirm_delete.html', {'user': user})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return redirect('user_list')

# Klaster Views
class KlasterListView(View):
    def get(self, request):
        klaster = Klaster.objects.all()
        return render(request, 'klaster_list.html', {'klaster': klaster})

class KlasterCreateView(View):
    def get(self, request):
        form = KlasterForm()
        return render(request, 'klaster_form.html', {'form': form})

    def post(self, request):
        form = KlasterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('klaster_list')
        return render(request, 'klaster_form.html', {'form': form})

class KlasterUpdateView(View):
    def get(self, request, pk):
        klaster = get_object_or_404(Klaster, pk=pk)
        form = KlasterForm(instance=klaster)
        return render(request, 'klaster_form.html', {'form': form})

    def post(self, request, pk):
        klaster = get_object_or_404(Klaster, pk=pk)
        form = KlasterForm(request.POST, instance=klaster)
        if form.is_valid():
            form.save()
            return redirect('klaster_list')
        return render(request, 'klaster_form.html', {'form': form})

class KlasterDeleteView(View):
    def get(self, request, pk):
        klaster = get_object_or_404(Klaster, pk=pk)
        return render(request, 'klaster_confirm_delete.html', {'klaster': klaster})

    def post(self, request, pk):
        klaster = get_object_or_404(Klaster, pk=pk)
        klaster.delete()
        return redirect('klaster_list')

# Indikator Views
class IndikatorListView(View):
    def get(self, request):
        indikator = Indikator.objects.all()
        return render(request, 'indikator_list.html', {'indikator': indikator})

class IndikatorCreateView(View):
    def get(self, request):
        form = IndikatorForm()
        return render(request, 'indikator_form.html', {'form': form})

    def post(self, request):
        form = IndikatorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('indikator_list')
        return render(request, 'indikator_form.html', {'form': form})

class IndikatorUpdateView(View):
    def get(self, request, pk):
        indikator = get_object_or_404(Indikator, pk=pk)
        form = IndikatorForm(instance=indikator)
        return render(request, 'indikator_form.html', {'form': form})

    def post(self, request, pk):
        indikator = get_object_or_404(Indikator, pk=pk)
        form = IndikatorForm(request.POST, instance=indikator)
        if form.is_valid():
            form.save()
            return redirect('indikator_list')
        return render(request, 'indikator_form.html', {'form': form})

class IndikatorDeleteView(View):
    def get(self, request, pk):
        indikator = get_object_or_404(Indikator, pk=pk)
        return render(request, 'indikator_confirm_delete.html', {'indikator': indikator})

    def post(self, request, pk):
        indikator = get_object_or_404(Indikator, pk=pk)
        indikator.delete()
        return redirect('indikator_list')

# Pilihan Views
# class PilihanListView(View):
#     def get(self, request):
#         pilihan = Pilihan.objects.all()
#         return render(request, 'pilihan_list.html', {'pilihan': pilihan})

# class PilihanCreateView(View):
#     def get(self, request):
#         form = PilihanForm()
#         return render(request, 'pilihan_form.html', {'form': form})

#     def post(self, request):
#         form = PilihanForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('pilihan_list')
#         return render(request, 'pilihan_form.html', {'form': form})

# class PilihanUpdateView(View):
#     def get(self, request, pk):
#         pilihan = get_object_or_404(Pilihan, pk=pk)
#         form = PilihanForm(instance=pilihan)
#         return render(request, 'pilihan_form.html', {'form': form})

#     def post(self, request, pk):
#         pilihan = get_object_or_404(Pilihan, pk=pk)
#         form = PilihanForm(request.POST, instance=pilihan)
#         if form.is_valid():
#             form.save()
#             return redirect('pilihan_list')
#         return render(request, 'pilihan_form.html', {'form': form})

# class PilihanDeleteView(View):
#     def get(self, request, pk):
#         pilihan = get_object_or_404(Pilihan, pk=pk)
#         return render(request, 'pilihan_confirm_delete.html', {'pilihan': pilihan})

#     def post(self, request, pk):
#         pilihan = get_object_or_404(Pilihan, pk=pk)
#         pilihan.delete()
#         return redirect('pilihan_list')

# Jawaban Views
class JawabanListView(View):
    def get(self, request):
        jawaban = Jawaban.objects.all()
        return render(request, 'jawaban_list.html', {'jawaban': jawaban})

class JawabanCreateView(View):
    def get(self, request):
        form = JawabanForm()
        return render(request, 'jawaban_form.html', {'form': form})

    def post(self, request):
        form = JawabanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('jawaban_list')
        return render(request, 'jawaban_form.html', {'form': form})

class JawabanUpdateView(View):
    def get(self, request, pk):
        jawaban = get_object_or_404(Jawaban, pk=pk)
        form = JawabanForm(instance=jawaban)
        return render(request, 'jawaban_form.html', {'form': form})

    def post(self, request, pk):
        jawaban = get_object_or_404(Jawaban, pk=pk)
        form = JawabanForm(request.POST, instance=jawaban)
        if form.is_valid():
            form.save()
            return redirect('jawaban_list')
        return render(request, 'jawaban_form.html', {'form': form})

class JawabanDeleteView(View):
    def get(self, request, pk):
        jawaban = get_object_or_404(Jawaban, pk=pk)
        return render(request, 'jawaban_confirm_delete.html', {'jawaban': jawaban})

    def post(self, request, pk):
        jawaban = get_object_or_404(Jawaban, pk=pk)
        jawaban.delete()
        return redirect('jawaban_list')

# Notifikasi Views
class NotifikasiListView(View):
    def get(self, request):
        notifikasi = Notifikasi.objects.all()
        return render(request, 'notifikasi_list.html', {'notifikasi': notifikasi})

class NotifikasiCreateView(View):
    def get(self, request):
        form = NotifikasiForm()
        return render(request, 'notifikasi_form.html', {'form': form})

    def post(self, request):
        form = NotifikasiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notifikasi_list')
        return render(request, 'notifikasi_form.html', {'form': form})

class NotifikasiUpdateView(View):
    def get(self, request, pk):
        notifikasi = get_object_or_404(Notifikasi, pk=pk)
        form = NotifikasiForm(instance=notifikasi)
        return render(request, 'notifikasi_form.html', {'form': form})

    def post(self, request, pk):
        notifikasi = get_object_or_404(Notifikasi, pk=pk)
        form = NotifikasiForm(request.POST, instance=notifikasi)
        if form.is_valid():
            form.save()
            return redirect('notifikasi_list')
        return render(request, 'notifikasi_form.html', {'form': form})

class NotifikasiDeleteView(View):
    def get(self, request, pk):
        notifikasi = get_object_or_404(Notifikasi, pk=pk)
        return render(request, 'notifikasi_confirm_delete.html', {'notifikasi': notifikasi})

    def post(self, request, pk):
        notifikasi = get_object_or_404(Notifikasi, pk=pk)
        notifikasi.delete()
        return redirect('notifikasi_list')

# Jawaban Final Views
class JawabanFinalListView(View):
    def get(self, request):
        jawaban_final = JawabanFinal.objects.all()
        return render(request, 'jawaban_final_list.html', {'jawaban_final': jawaban_final})

class JawabanFinalCreateView(View):
    def get(self, request):
        form = JawabanFinalForm()
        return render(request, 'jawaban_final_form.html', {'form': form})

    def post(self, request):
        form = JawabanFinalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('jawaban_final_list')
        return render(request, 'jawaban_final_form.html', {'form': form})

class JawabanFinalUpdateView(View):
    def get(self, request, pk):
        jawaban_final = get_object_or_404(JawabanFinal, pk=pk)
        form = JawabanFinalForm(instance=jawaban_final)
        return render(request, 'jawaban_final_form.html', {'form': form})

    def post(self, request, pk):
        jawaban_final = get_object_or_404(JawabanFinal, pk=pk)
        form = JawabanFinalForm(request.POST, instance=jawaban_final)
        if form.is_valid():
            form.save()
            return redirect('jawaban_final_list')
        return render(request, 'jawaban_final_form.html', {'form': form})

class JawabanFinalDeleteView(View):
    def get(self, request, pk):
        jawaban_final = get_object_or_404(JawabanFinal, pk=pk)
        return render(request, 'jawaban_final_confirm_delete.html', {'jawaban_final': jawaban_final})

    def post(self, request, pk):
        jawaban_final = get_object_or_404(JawabanFinal, pk=pk)
        jawaban_final.delete()
        return redirect('jawaban_final_list')

# User Log Views
class UserLogListView(View):
    def get(self, request):
        user_logs = UserLog.objects.all()
        return render(request, 'user_log_list.html', {'user_logs': user_logs})

class UserLogCreateView(View):
    def get(self, request):
        form = UserLogForm()
        return render(request, 'user_log_form.html', {'form': form})

    def post(self, request):
        form = UserLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_log_list')
        return render(request, 'user_log_form.html', {'form': form})

class UserLogUpdateView(View):
    def get(self, request, pk):
        user_log = get_object_or_404(UserLog, pk=pk)
        form = UserLogForm(instance=user_log)
        return render(request, 'user_log_form.html', {'form': form})

    def post(self, request, pk):
        user_log = get_object_or_404(UserLog, pk=pk)
        form = UserLogForm(request.POST, instance=user_log)
        if form.is_valid():
            form.save()
            return redirect('user_log_list')
        return render(request, 'user_log_form.html', {'form': form})

class UserLogDeleteView(View):
    def get(self, request, pk):
        user_log = get_object_or_404(UserLog, pk=pk)
        return render(request, 'user_log_confirm_delete.html', {'user_log': user_log})

    def post(self, request, pk):
        user_log = get_object_or_404(UserLog, pk=pk)
        user_log.delete()
        return redirect('user_log_list')
    
@csrf_exempt
@login_required    
def get_file(request, filename):
    # Tentukan path ke folder uploads
    upload_folder = os.path.join(settings.BASE_DIR, 'media/uploads')
    
    # Path lengkap ke file yang ingin ditampilkan
    file_path = os.path.join(upload_folder, filename)

    # Pastikan file ada
    if os.path.exists(file_path):
        # Menebak tipe MIME file (misalnya image/jpeg, application/pdf)
        mime_type, _ = guess_type(file_path)
        
        # Buka file untuk membaca dalam mode biner
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=mime_type)
            return response
    else:
        raise Http404("File not found")
