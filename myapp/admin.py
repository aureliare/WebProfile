from django.contrib import admin
from .models import (
    Instansi, User, Klaster, Indikator, Form, Pertanyaan,
    FilePertanyaan, MasterPilihan, Pilihan, PertanyaanInstansi, FilePertanyaanInstansi, Jawaban, FileJawaban, Notifikasi,
    JawabanFinal, UserLog
)

class InstansiAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('name',)  # Added comma

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'instansi', 'created_at', 'updated_at')
    list_filter = ('role', 'instansi')
    search_fields = ('username',)  # Added comma

class KlasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('name',)  # Added comma

class IndikatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'klaster', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('klaster',)  # Added comma
    search_fields = ('name',)  # Added comma

class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'start', 'end', 'is_active', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('name',)  # Added comma
    list_filter = ('year',)  # Added comma

class PertanyaanAdmin(admin.ModelAdmin):
    list_display = ('name', 'indikator', 'type', 'category', 'description', 'evaluation_note', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('indikator', 'type')
    search_fields = ('text',)  # Added comma

class FilePertanyaanAdmin(admin.ModelAdmin):
    list_display = ('pertanyaan', 'file', 'original_filename', 'encrypted_filename', 'file_extension', 'url', 'path', 'content_type', 'created_at', 'updated_at')
    search_fields = ('pertanyaan__name',)  # Added comma

class MasterPilihanAdmin(admin.ModelAdmin):
    list_display = ('name', 'bobot', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('text',)  # Added comma

class PilihanAdmin(admin.ModelAdmin):
    list_display = ('master_pilihan', 'pertanyaan', 'bobot', 'order', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('master_pilihan', 'pertanyaan')
    search_fields = ('master_pilihan__name',)  # Added comma

class PertanyaanInstansiAdmin(admin.ModelAdmin):
    list_display = ('pertanyaan', 'type', 'category', 'form', 'instansi', 'order', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('pertanyaan', 'type', 'form', 'instansi')
    search_fields = ('pertanyaan__name',)  # Added comma

class FilePertanyaanInstansiAdmin(admin.ModelAdmin):
    list_display = ('pertanyaan_instansi', 'file', 'original_filename', 'encrypted_filename', 'file_extension', 'url', 'path', 'content_type', 'created_at', 'updated_at')
    search_fields = ('pertanyaan_instansi__pertanyaan__name',)  # Added comma

class JawabanAdmin(admin.ModelAdmin):
    list_display = ('user', 'instansi', 'pertanyaan_instansi', 'pertanyaan', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('user', 'instansi', 'pertanyaan_instansi', 'pertanyaan')
    search_fields = ('user__username', 'instansi__name', 'pertanyaan__name')

class FileJawabanAdmin(admin.ModelAdmin):
    list_display = ('user', 'instansi', 'jawaban', 'file', 'original_filename', 'encrypted_filename', 'file_extension', 'url', 'path', 'content_type', 'created_at', 'updated_at')
    list_filter = ('user', 'instansi')
    search_fields = ('jawaban__user__username',)  # Added comma

class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ('user', 'jawaban', 'type', 'is_read', 'created_at')
    list_filter = ('is_read', 'type')
    search_fields = ('user__username',)

class JawabanFinalAdmin(admin.ModelAdmin):
    list_display = ('verifikator', 'user', 'instansi', 'jawaban', 'status', 'bobot', 'created_at', 'updated_at', 'deleted_at')
    list_filter = ('verifikator__username', 'user__username', 'instansi__name', 'status')
    search_fields = ('jawaban__user__username',)

class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'details')
    list_filter = ('action', 'user')
    search_fields = ('user__username',)

# Register models with the admin site
admin.site.register(Instansi, InstansiAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Klaster, KlasterAdmin)
admin.site.register(Indikator, IndikatorAdmin)
admin.site.register(Form, FormAdmin)
admin.site.register(Pertanyaan, PertanyaanAdmin)
admin.site.register(FilePertanyaan, FilePertanyaanAdmin)
admin.site.register(MasterPilihan, MasterPilihanAdmin)
admin.site.register(Pilihan, PilihanAdmin)
admin.site.register(PertanyaanInstansi, PertanyaanInstansiAdmin)
admin.site.register(FilePertanyaanInstansi, FilePertanyaanInstansiAdmin)
admin.site.register(Jawaban, JawabanAdmin)
admin.site.register(FileJawaban, FileJawabanAdmin)
admin.site.register(Notifikasi, NotifikasiAdmin)
admin.site.register(JawabanFinal, JawabanFinalAdmin)
admin.site.register(UserLog, UserLogAdmin)
