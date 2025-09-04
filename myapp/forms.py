from django import forms
from .models import (
    Instansi, User, Klaster, Indikator, Form,
    Pertanyaan, Pilihan, Jawaban, Notifikasi, JawabanFinal
)
from captcha.fields import CaptchaField

class LoginForm(forms.Form):
    username = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    role = forms.ChoiceField(choices=[('', 'Pilih Role'), ('admin', 'Admin'), ('verifikator', 'Verifikator'), ('user', 'User')], required=True)
    captcha = CaptchaField()

class UserLogForm(forms.Form):
    """Form untuk login pengguna."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Tambahkan validasi tambahan jika diperlukan
        return username

class InstansiForm(forms.ModelForm):
    class Meta:
        model = Instansi
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Instansi'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Nama instansi tidak boleh kosong.")
        return name


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Kata Sandi'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'instansi', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Pengguna'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'instansi': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(),
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Nama pengguna sudah terdaftar.")
        return username


class KlasterForm(forms.ModelForm):
    class Meta:
        model = Klaster
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Klaster'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Nama klaster tidak boleh kosong.")
        return name


class IndikatorForm(forms.ModelForm):
    class Meta:
        model = Indikator
        fields = ['name', 'klaster']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Indikator'}),
            'klaster': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Nama indikator tidak boleh kosong.")
        return name


class FormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['name', 'year', 'start', 'end', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Form'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tahun'}),
        }
    
    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year < 2000 or year > 2100:
            raise forms.ValidationError("Tahun harus antara 2000 dan 2100.")
        return year


class PertanyaanForm(forms.ModelForm):
    class Meta:
        model = Pertanyaan
        fields = ['name', 'indikator', 'type', 'description']
        widgets = {
            'name': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Isi Pertanyaan', 'rows': 3}),
            'indikator': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Penjelasan', 'rows': 2}),
        }
    
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise forms.ValidationError("Pertanyaan tidak boleh kosong.")
        return text


class PilihanForm(forms.ModelForm):
    class Meta:
        model = Pilihan
        fields = ['master_pilihan', 'pertanyaan', 'bobot', 'order']
        widgets = {
            'master_pilihan': forms.Select(attrs={'class': 'form-control'}),
            'pertanyaan': forms.Select(attrs={'class': 'form-control'}),
            'bobot': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bobot'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Urutan'}),
        }
    
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise forms.ValidationError("Pilihan tidak boleh kosong.")
        return text


class JawabanForm(forms.ModelForm):
    class Meta:
        model = Jawaban
        fields = ['user', 'pertanyaan', 'pilihan', 'text_jawaban', 'bobot']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'pertanyaan': forms.Select(attrs={'class': 'form-control'}),
            'pilihan': forms.Select(attrs={'class': 'form-control'}),
            'text_jawaban': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Jawaban', 'rows': 3}),
            'bobot': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bobot'}),
        }
    
    def clean_text_jawaban(self):
        text_jawaban = self.cleaned_data.get('text_jawaban')
        if not text_jawaban:
            raise forms.ValidationError("Jawaban tidak boleh kosong.")
        return text_jawaban


class NotifikasiForm(forms.ModelForm):
    class Meta:
        model = Notifikasi
        fields = ['user', 'jawaban', 'type', 'is_read']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'jawaban': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'is_read': forms.CheckboxInput(),
        }


class JawabanFinalForm(forms.ModelForm):
    class Meta:
        model = JawabanFinal
        fields = ['jawaban', 'user', 'pilihan', 'bobot', 'catatan', 'status']
        widgets = {
            'jawaban': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'pilihan': forms.Select(attrs={'class': 'form-control'}),
            'bobot': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bobot'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Catatan', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_catatan(self):
        catatan = self.cleaned_data.get('catatan')
        if not catatan:
            raise forms.ValidationError("Catatan tidak boleh kosong.")
        return catatan
