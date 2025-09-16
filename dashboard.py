import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# Konfigurasi Halaman Dashboard
# =============================================================================
st.set_page_config(
    page_title="Dashboard Rekapitulasi Permohonan",
    page_icon="📊",
    layout="wide"
)
# --- BAGIAN BARU UNTUK BACKGROUND GAMBAR ---
# Pastikan jalur gambar sudah benar.
# Jika gambar ada di folder yang sama dengan dashboard.py: "kantor_imigrasi.jpeg"
# Jika gambar ada di subfolder 'images': "images/kantor_imigrasi.jpeg"
background_image_path = "kanim.jpe" 

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{
            base64.b64encode(open(background_image_path, "rb").read()).decode()
        }");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
        opacity: 0.5; /* Tingkat opasitas 50% */
    }}
    .stApp > header {{
        background-color: rgba(0,0,0,0); /* Membuat header transparan */
    }}
    </style>
    """,
    unsafe_allow_html=True
)
import base64 # <-- Pastikan import base64 ditambahkan di awal
# ------------------------------------------

st.title('📊 Dashboard Rekapitulasi Data Permohonan')
st.write('Dashboard ini digunakan untuk memantau status permohonan yang masuk.')

# =============================================================================
# Fungsi Bantuan
# =============================================================================

def hitung_hari_kerja(tanggal_awal):
    if pd.isna(tanggal_awal):
        return 0
    tanggal_akhir = pd.Timestamp.now().normalize()
    return np.busday_count(tanggal_awal.date(), tanggal_akhir.date())

def highlight_lebih_3_hari(row):
    if row['Lama Proses (Hari Kerja)'] > 3:
        return ['background-color: #FFCDD2'] * len(row)
    else:
        return [''] * len(row)

# =============================================================================
# Fungsi untuk Memuat Data dengan Caching
# =============================================================================
@st.cache_data
def load_and_prepare_data(csv_path):
    print("--- Menjalankan fungsi load_and_prepare_data (ini hanya akan muncul sekali) ---")
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    df['Tanggal Permohonan'] = pd.to_datetime(df['Tanggal Permohonan'], errors='coerce')
    df.dropna(subset=['Tanggal Permohonan'], inplace=True)
    df['Lama Proses (Hari Kerja)'] = df['Tanggal Permohonan'].apply(hitung_hari_kerja)
    
    return df

# =============================================================================
# Logika Utama Aplikasi
# =============================================================================
try:
    df = load_and_prepare_data('data_imigrasi.csv')

    if df.empty:
        st.error("Tidak ada data valid yang bisa ditampilkan. Mohon jalankan 'scraper.py' terlebih dahulu atau periksa isi file CSV Anda.")
    else:
        # --- Bagian UI dan Filter ---
        st.header('Filter Data Permohonan')
        
        today = datetime.now()
        one_month_ago = (today - pd.DateOffset(months=1)).date()
        min_data_date = df['Tanggal Permohonan'].min().date()
        default_start_date = max(one_month_ago, min_data_date)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Dari Tanggal", value=default_start_date)
        with col2:
            end_date = st.date_input("Sampai Tanggal", value=today.date())

        # Ambil semua opsi unik yang tersedia di data
        layanan_options = sorted(df['Layanan'].unique())
        kategori_options = sorted(df['Kategori Produk'].unique())
        posisi_options = sorted(df['Posisi Permohonan'].unique())

        # --- PERUBAHAN UNTUK FILTER DEFAULT ---
        # Tentukan daftar default yang Anda inginkan
        default_layanan = ["CONVERSION", "EXTEND", "IMKAPPLICATION", "ITKT"]
        default_kategori = ["ITAP", "ITK", "ITKT", "Multiple Exit Re-entry Permit", "Stay Permit"]
        default_posisi = ["Role : KANIM", "Role : KAKANIM", "Role : EXTEND_DITJENIM", "Role : ALTUS_DITJENIM"]

        # Filter daftar default untuk memastikan semua opsi ada di data (mencegah error)
        actual_default_layanan = [opt for opt in default_layanan if opt in layanan_options]
        actual_default_kategori = [opt for opt in default_kategori if opt in kategori_options]
        actual_default_posisi = [opt for opt in default_posisi if opt in posisi_options]
        # ------------------------------------

        col3, col4 = st.columns(2)
        with col3:
            selected_layanan = st.multiselect(
                'Pilih Layanan:',
                options=layanan_options,
                default=actual_default_layanan # <-- Menggunakan default baru
            )
        with col4:
            selected_kategori = st.multiselect(
                'Pilih Kategori Produk:',
                options=kategori_options,
                default=actual_default_kategori # <-- Menggunakan default baru
            )
            
        selected_posisi = st.multiselect(
            'Pilih Posisi Permohonan:',
            options=posisi_options,
            default=actual_default_posisi # <-- Menggunakan default baru
        )
            
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

        filtered_df = df[
            (df['Tanggal Permohonan'] >= start_datetime) & (df['Tanggal Permohonan'] < end_datetime) &
            (df['Layanan'].isin(selected_layanan)) &
            (df['Kategori Produk'].isin(selected_kategori)) &
            (df['Posisi Permohonan'].isin(selected_posisi))
        ]

        st.header(f"Menampilkan {len(filtered_df)} Permohonan")
        st.write("Permohonan yang diproses lebih dari 3 hari kerja akan ditandai dengan warna merah muda.")
        
        st.dataframe(
            filtered_df.style.apply(highlight_lebih_3_hari, axis=1),
            use_container_width=True
        )

except FileNotFoundError:
    st.error("File 'data_imigrasi.csv' tidak ditemukan. Pastikan Anda sudah menjalankan 'scraper.py' untuk mengambil data terlebih dahulu.")
except Exception as e:
    st.error(f"Terjadi error saat memproses data: {e}")


