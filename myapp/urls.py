from django.urls import path, include
from . import views
from .views import UserLoginView, LogoutView

urlpatterns = [
    # login
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('password_reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('webprofile/', views.webprofile_view, name='webprofile'),

    # URL untuk halaman utama
    path('', views.home_view, name='home'),


    # URL untuk halaman profile dropdown
    path('profile-pejabat/', views.profile_pejabat_view, name='profile_pejabat'),
    path('tugas-pokok-fungsi/', views.tugas_pokok_fungsi_view, name='tugas_pokok_fungsi'),
    path('struktur-organisasi/', views.struktur_organisasi_view, name='struktur_organisasi'),


    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Instansi
    path('admin/instansi/', views.InstansiListView.as_view(), name='instansi_list'),
    # path('admin/instansi/create/', views.InstansiCreateView.as_view(), name='instansi_create'),
    # path('admin/instansi/<int:pk>/update/', views.InstansiUpdateView.as_view(), name='instansi_update'),
    # path('admin/instansi/<int:pk>/delete/', views.InstansiDeleteView.as_view(), name='instansi_delete'),

    # Pengguna
    path('admin/pengguna/', views.PenggunaListView.as_view(), name='pengguna_list'),

     # Form
    path('admin/form/', views.FormListView.as_view(), name='form_list'),

    # Master Pilihan
    path('admin/master_pilihan/', views.MasterPilihanListView.as_view(), name='masterpilihan_list'),

    # Pertanyaan
    path('admin/pertanyaan/', views.PertanyaanListView.as_view(), name='pertanyaan_list'),

    # Pilihan
    path('admin/pilihan/', views.PilihanListView.as_view(), name='pilihan_list'),

    # Pertanyaan Baku
    path('admin/pertanyaan_baku/', views.PertanyaanBakuListView.as_view(), name='pertanyaan_baku_list'),

    # Pertanyaan Spesifik
    path('admin/pertanyaan_spesifik/', views.PertanyaanSpesifikListView.as_view(), name='pertanyaan_spesifik_list'),

    # Buku Panduan
    path('admin/buku_panduan/', views.BukuPanduanListView.as_view(), name='buku_panduan_list'),

    # Petunjuk Teknis
    path('admin/petunjuk_teknis/', views.PetunjukTeknisListView.as_view(), name='petunjuk_teknis_list'),

    # User
    # path('admin/user/', views.UserListView.as_view(), name='user_list'),
    # path('admin/user/create/', views.UserCreateView.as_view(), name='user_create'),
    # path('admin/user/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    # path('admin/user/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # Klaster
    # path('admin/klaster/', views.KlasterListView.as_view(), name='klaster_list'),
    # path('admin/klaster/create/', views.KlasterCreateView.as_view(), name='klaster_create'),
    # path('admin/klaster/<int:pk>/update/', views.KlasterUpdateView.as_view(), name='klaster_update'),
    # path('admin/klaster/<int:pk>/delete/', views.KlasterDeleteView.as_view(), name='klaster_delete'),

    # Indikator
    # path('admin/indikator/', views.IndikatorListView.as_view(), name='indikator_list'),
    # path('admin/indikator/create/', views.IndikatorCreateView.as_view(), name='indikator_create'),
    # path('admin/indikator/<int:pk>/update/', views.IndikatorUpdateView.as_view(), name='indikator_update'),
    # path('admin/indikator/<int:pk>/delete/', views.IndikatorDeleteView.as_view(), name='indikator_delete'),

    # Form
    # path('admin/form/', views.FormListView.as_view(), name='form_list'),
    # path('admin/form/create/', views.FormCreateView.as_view(), name='form_create'),
    # path('admin/form/<int:pk>/update/', views.FormUpdateView.as_view(), name='form_update'),
    # path('admin/form/<int:pk>/delete/', views.FormDeleteView.as_view(), name='form_delete'),

    # Pertanyaan
    # path('admin/pertanyaan/', views.PertanyaanListView.as_view(), name='pertanyaan_list'),
    # path('admin/pertanyaan/create/', views.PertanyaanCreateView.as_view(), name='admin/pertanyaan_create'),
    # path('admin/pertanyaan/<int:pk>/update/', views.PertanyaanUpdateView.as_view(), name='pertanyaan_update'),
    # path('admin/pertanyaan/<int:pk>/delete/', views.PertanyaanDeleteView.as_view(), name='pertanyaan_delete'),

    # Pilihan
    # path('admin/pilihan/', views.PilihanListView.as_view(), name='pilihan_list'),
    # path('admin/pilihan/create/', views.PilihanCreateView.as_view(), name='pilihan_create'),
    # path('admin/pilihan/<int:pk>/update/', views.PilihanUpdateView.as_view(), name='pilihan_update'),
    # path('admin/pilihan/<int:pk>/delete/', views.PilihanDeleteView.as_view(), name='pilihan_delete'),

    # Jawaban
    # path('admin/jawaban/', views.JawabanListView.as_view(), name='jawaban_list'),
    # path('admin/jawaban/create/', views.JawabanCreateView.as_view(), name='jawaban_create'),
    # path('admin/jawaban/<int:pk>/update/', views.JawabanUpdateView.as_view(), name='jawaban_update'),
    # path('admin/jawaban/<int:pk>/delete/', views.JawabanDeleteView.as_view(), name='jawaban_delete'),

    # Notifikasi
    # path('admin/notifikasi/', views.NotifikasiListView.as_view(), name='notifikasi_list'),
    # path('admin/notifikasi/create/', views.NotifikasiCreateView.as_view(), name='notifikasi_create'),
    # path('admin/notifikasi/<int:pk>/update/', views.NotifikasiUpdateView.as_view(), name='admin/notifikasi_update'),
    # path('admin/notifikasi/<int:pk>/delete/', views.NotifikasiDeleteView.as_view(), name='notifikasi_delete'),

    # Jawaban Final
    # path('admin/jawaban-final/', views.JawabanFinalListView.as_view(), name='jawaban_final_list'),
    # path('admin/jawaban-final/create/', views.JawabanFinalCreateView.as_view(), name='jawaban_final_create'),
    # path('admin/jawaban-final/<int:pk>/update/', views.JawabanFinalUpdateView.as_view(), name='jawaban_final_update'),
    # path('admin/jawaban-final/<int:pk>/delete/', views.JawabanFinalDeleteView.as_view(), name='jawaban_final_delete'),

    # User Log
    path('admin/user-log/', views.UserLogListView.as_view(), name='user_log_list'),

    path('user/dashboard/', views.UserDashboardView.as_view(), name='user_dashboard'),
    
    path('operator/dashboard/', views.OperatorDashboardView.as_view(), name='operator_dashboard'),

    path('verifikator/dashboard/', views.VerifikatorDashboardView.as_view(), name='verifikator_dashboard'),

    # API
    path('api/pengguna/', views.pengguna_data, name="pengguna_data"),
    path('api/instansi/', views.instansi_data, name="instansi_data"),
    path('api/form/', views.form_data, name="form_data"),
    path('api/tahun/', views.tahun_data, name="tahun_data"),
    path('api/master_pilihan/', views.masterpilihan_data, name="masterpilihan_data"),
    path('api/pertanyaan/', views.pertanyaan_data, name="pertanyaan_data"),
    path('api/buku_panduan/', views.buku_panduan_data, name="buku_panduan_data"),
    path('api/petunjuk_teknis/', views.petunjuk_teknis_data, name="petunjuk_teknis_data"),
    path('api/file_pertanyaan/', views.filepertanyaan_data, name="filepertanyaan_data"),
    path('api/pilihan_pertanyaan/', views.pilihan_data, name="pilihan_data"),
    path('api/pertanyaan_baku/', views.pertanyaan_baku_data, name="pertanyaan_baku_data"),
    path('api/file_pertanyaan_instansi/', views.filepertanyaaninstansi_data, name="filepertanyaaninstansi_data"),
    path('api/pertanyaan_spesifik/', views.pertanyaan_spesifik_data, name="pertanyaan_spesifik_data"),
    path('api/pertanyaan_spesifik_get/', views.get_questions, name="pertanyaan_spesifik_get"),
    path('api/pertanyaan_spesifik_post/', views.save_choice, name="pertanyaan_spesifik_post"),
    path('api/file_jawaban/', views.filejawaban_data, name="filejawaban_data"),
    path('api/pertanyaan_baku_get/', views.get_questions, name="pertanyaan_baku_get"),
    path('api/pertanyaan_baku_post/', views.save_choice, name="pertanyaan_baku_post"),
    path('api/akumulasi_data/', views.akumulasi_data, name="akumulasi_data"),
    path('api/lihat_hasil/', views.lihat_hasil, name="lihat_hasil"),

    # Data Admin
    path('admin/data-spesifik/', views.dataSpesifikView.as_view(), name="admin_data_spesifik"),
    path('admin/data-baku/', views.dataBakuView.as_view(), name="admin_data_baku"),
    path('admin/hasil-akumulasi/', views.hasilAkumulasiView.as_view(), name="admin_hasil_akumulasi"),
    path('admin/hasil-penilaian/', views.hasilAkumulasiView.as_view(), name="admin_hasil_penilaian"),
    path('admin/lihat-hasil/', views.lihatHasilView.as_view(), name="admin_lihat_hasil"),
    path('admin/penilaian-perangkat-daerah/', views.penilaianPerangkatDaerahView.as_view(), name="admin_penilaian_perangkat_daerah"),
    path('admin/data-general/', views.dataGeneralView.as_view(), name="admin_data_general"),
    path('admin/data-general-detail/', views.dataGeneralDetailView.as_view(), name="admin_data_general_detail"),
    path('admin/data-general-post/', views.save_correction, name="admin_data_general_post"),
    path('admin/penilaian-perangkat-daerah-detail/', views.penilaianPerangkatDaerahDetailView.as_view(), name="admin_penilaian_perangkat_daerah_detail"),
    path('admin/daftar-notifikasi/', views.NotifikasiListViewNew.as_view(), name="admin_daftar_notifikasi"),

    # Data Verifikator
    path('verifikator/data-spesifik/', views.dataSpesifikView.as_view(), name="verifikator_data_spesifik"),
    path('verifikator/data-baku/', views.dataBakuView.as_view(), name="verifikator_data_baku"),
    path('verifikator/lihat-hasil/', views.lihatHasilView.as_view(), name="verifikator_lihat_hasil"),
    path('verifikator/hasil-akumulasi/', views.hasilAkumulasiView.as_view(), name="verifikator_hasil_akumulasi"),
    path('verifikator/hasil-penilaian/', views.hasilAkumulasiView.as_view(), name="verifikator_hasil_penilaian"),
    path('verifikator/penilaian-perangkat-daerah/', views.penilaianPerangkatDaerahView.as_view(), 
    name="verifikator_penilaian_perangkat_daerah"),
    path('verifikator/data-general/', views.dataGeneralView.as_view(), name="verifikator_data_general"),
    path('verifikator/data-general-detail/', views.dataGeneralDetailView.as_view(), name="verifikator_data_general_detail"),
    path('verifikator/data-general-post/', views.save_correction, name="verifikator_data_general_post"),
    path('verifikator/penilaian-perangkat-daerah-detail/', views.penilaianPerangkatDaerahDetailView.as_view(), name="verifikator_penilaian_perangkat_daerah_detail"),
    path('verifikator/daftar-notifikasi/', views.NotifikasiListViewNew.as_view(), name="verifikator_daftar_notifikasi"),

    # Data User
    path('user/data-spesifik/', views.dataSpesifikView.as_view(), name="user_data_spesifik"),
    path('user/data-baku/', views.dataBakuView.as_view(), name="user_data_baku"),
    path('user/hasil-akumulasi/', views.hasilAkumulasiView.as_view(), name="user_hasil_akumulasi"),
    path('user/hasil-penilaian/', views.hasilAkumulasiView.as_view(), name="user_hasil_penilaian"),
    path('user/lihat-hasil/', views.lihatHasilView.as_view(), name="user_lihat_hasil"),
    path('user/penilaian-perangkat-daerah/', views.penilaianPerangkatDaerahView.as_view(), name="user_penilaian_perangkat_daerah"),
    path('user/data-general/', views.dataGeneralView.as_view(), name="user_data_general"),
    path('user/data-general-detail/', views.dataGeneralDetailView.as_view(), name="user_data_general_detail"),
    path('user/data-general-post/', views.save_correction, name="user_data_general_post"),
    path('user/penilaian-perangkat-daerah-detail/', views.penilaianPerangkatDaerahDetailView.as_view(), name="user_penilaian_perangkat_daerah_detail"),
    path('user/daftar-notifikasi/', views.NotifikasiListViewNew.as_view(), name="user_daftar_notifikasi"),
    path('kla-data/<str:filename>/', views.get_file, name='get_file'),

    # Data operator
    path('operator/data-spesifik/', views.dataSpesifikView.as_view(), name="operator_data_spesifik"),
    path('operator/data-baku/', views.dataBakuView.as_view(), name="operator_data_baku"),
    path('operator/hasil-akumulasi/', views.hasilAkumulasiView.as_view(), name="operator_hasil_akumulasi"),
    path('operator/hasil-penilaian/', views.hasilAkumulasiView.as_view(), name="operator_hasil_penilaian"),
    path('operator/lihat-hasil/', views.lihatHasilView.as_view(), name="operator_lihat_hasil"),
    path('operator/penilaian-perangkat-daerah/', views.penilaianPerangkatDaerahView.as_view(), name="operator_penilaian_perangkat_daerah"),
    path('operator/data-general/', views.dataGeneralView.as_view(), name="operator_data_general"),
    path('operator/data-general-detail/', views.dataGeneralDetailView.as_view(), name="operator_data_general_detail"),
    path('operator/data-general-post/', views.save_correction, name="operator_data_general_post"),
    path('operator/penilaian-perangkat-daerah-detail/', views.penilaianPerangkatDaerahDetailView.as_view(), name="operator_penilaian_perangkat_daerah_detail"),
    path('operator/daftar-notifikasi/', views.NotifikasiListViewNew.as_view(), name="operator_daftar_notifikasi"),
    path('kla-data/<str:filename>/', views.get_file, name='get_file'),
]
