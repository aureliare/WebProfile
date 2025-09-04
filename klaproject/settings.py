import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-7%&h=e$1p9&15#$@4d-k*494inv)=6bqa36w+%vbaom9o-xtra'
DEBUG = True
ALLOWED_HOSTS = []  # Tambahkan domain atau IP jika sudah siap deploy

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',  # Tambahkan aplikasi kustom Anda di sini
    'captcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'klaproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'klaproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'klaproject',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost', 
        'PORT': '3306',       
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'id-ID'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'  # Memastikan STATIC_URL diawali '/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # Folder static yang kustom
STATIC_ROOT = BASE_DIR / "staticfiles"  # Tempat mengumpulkan file statis

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'myapp.User'

LOGIN_URL = '/kla/login/'  # Ganti dengan URL login Anda
LOGIN_REDIRECT_URL = '/instansi/'  # Ganti dengan URL setelah login
LOGOUT_REDIRECT_URL = '/kla/login/'  # Ganti dengan URL setelah logout

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Ganti dengan host SMTP Anda
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'bebelibekasikab@gmail.com'
EMAIL_HOST_PASSWORD = 'srrzpytrlaijeyoz'

# Pengaturan untuk django-simple-captcha
CAPTCHA_FONT_SIZE = 30  # Ukuran font untuk CAPTCHA
CAPTCHA_LENGTH = 3      # Jumlah karakter CAPTCHA
CAPTCHA_IMAGE_SIZE = (180, 40)  # Ukuran gambar CAPTCHA (lebar, tinggi)
CAPTCHA_NOISE_FUNCTION = 'captcha.helpers.noise_empty'  # Menentukan jenis noise (opsional)

# Jika Anda ingin menggunakan reCAPTCHA, Anda bisa mengonfigurasi ini
# CAPTCHA_FRONTEND = 'captcha.widgets.ReCaptchaV2Checkbox'

# # Pengaturan untuk django-simple-captcha
# CAPTCHA_FONT_SIZE = 20  # Ukuran font untuk CAPTCHA
# CAPTCHA_LENGTH = 3      # Jumlah karakter CAPTCHA
# CAPTCHA_IMAGE_SIZE = (180, 40)  # Ukuran gambar CAPTCHA (lebar, tinggi)
# CAPTCHA_NOISE_FUNCTION = 'captcha.helpers.noise_empty'  # Menentukan jenis noise (opsional)

# # Tambahkan pengaturan untuk hanya angka
# CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'  # Fungsi tantangan matematika, jika diinginkan
# CAPTCHA_IMAGE_GENERATOR = 'captcha.helpers.simple_captcha_image'  # Fungsi generator gambar
# CAPTCHA_TIMEOUT = 5  # Waktu habis untuk CAPTCHA dalam menit

# # Jika Anda ingin menggunakan fungsi khusus yang hanya mengizinkan angka:
# import string

# CAPTCHA_CHARSET = string.digits  # Menggunakan hanya karakter angka (0-9)

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Mengarah ke folder 'uploads'

X_FRAME_OPTIONS = 'ALLOW-FROM http://127.0.0.1:8000'
X_FRAME_OPTIONS = 'SAMEORIGIN'


