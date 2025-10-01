import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import base64
# =============================================================================
# Konfigurasi Halaman Dashboard
# =============================================================================
st.set_page_config(
    page_title="Dashboard Rekapitulasi Permohonan",
    page_icon="📊",
    layout="wide"
)
# --- BAGIAN UNTUK BACKGROUND GAMBAR (TIDAK DIUBAH) ---
background_image_path = "kanim.jpg"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:jpg;base64,{
            base64.b64encode(open(background_image_path, "rb").read()).decode()
        }");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
        opacity: 0.5;
    }}
    .stApp > header {{
        background-color: rgba(0,0,0,0);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

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

# --- PERUBAHAN 2: Fungsi highlight baru berdasarkan umur permohonan ---
def highlight_by_age(row):
    """
    Memberi warna latar belakang baris berdasarkan umur permohonan dalam hari kalender.
    - > 30 hari: hijau tua (#344e41) dengan teks putih.
    - > 3 hari: hijau muda (#a7c957).
    """
    umur_hari = row['Lama Proses (Hari Kalender)']
    style = ''
    # Cek dari kondisi terlama (paling spesifik) terlebih dahulu
    if umur_hari > 30:
        # Menambahkan 'color: white;' agar teks mudah dibaca di latar gelap
        style = 'background-color: #344e41; color: white;'
    elif umur_hari > 3:
        style = 'background-color: #a7c957'
    
    # Kembalikan style untuk diterapkan ke semua kolom di baris tersebut
    return [style] * len(row)

# =============================================================================
# Fungsi untuk Memuat Data dengan Caching
# =============================================================================
@st.cache_data
def load_and_prepare_data(csv_path):
    print("--- Memuat dan mempersiapkan data... ---")
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    df['Tanggal Permohonan'] = pd.to_datetime(df['Tanggal Permohonan'], errors='coerce')
    df.dropna(subset=['Tanggal Permohonan'], inplace=True)
    
    # Menghitung lama proses dalam hari kerja (tetap dipertahankan)
    df['Lama Proses (Hari Kerja)'] = df['Tanggal Permohonan'].apply(hitung_hari_kerja)
    
    # --- PERUBAHAN 2: Tambahkan kolom baru untuk umur dalam HARI KALENDER ---
    df['Lama Proses (Hari Kalender)'] = (pd.Timestamp.now().normalize() - df['Tanggal Permohonan']).dt.days
    
    return df

# =============================================================================
# Logika Utama Aplikasi
# =============================================================================
try:
    df = load_and_prepare_data('data_imigrasi.csv')

    if df.empty:
        st.error("Tidak ada data valid yang bisa ditampilkan. Mohon periksa file CSV Anda.")
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
        # --- PERUBAHAN 1: Ambil opsi untuk filter baru 'Jenis Produk' ---
        jenis_produk_options = sorted(df['Jenis Produk'].unique())
        
        # Opsi filter default (tetap dipertahankan untuk Layanan dan Kategori)
        default_layanan = ["CONVERSION", "EXTEND", "IMKAPPLICATION", "ITKT"]
        default_kategori = ["ITAP", "ITK", "ITKT", "Multiple Exit Re-entry Permit", "Stay Permit"]
        actual_default_layanan = [opt for opt in default_layanan if opt in layanan_options]
        actual_default_kategori = [opt for opt in default_kategori if opt in kategori_options]
        
        col3, col4 = st.columns(2)
        with col3:
            selected_layanan = st.multiselect(
                'Pilih Layanan:',
                options=layanan_options,
                default=actual_default_layanan
            )
        with col4:
            selected_kategori = st.multiselect(
                'Pilih Kategori Produk:',
                options=kategori_options,
                default=actual_default_kategori
            )
        
        # --- PERUBAHAN 1: Tambahkan widget multiselect untuk 'Jenis Produk' ---
        selected_jenis_produk = st.multiselect(
            'Pilih Jenis Produk:',
            options=jenis_produk_options,
            default=jenis_produk_options # Default memilih semua opsi yang ada
        )

        # --- PERUBAHAN 3: Ubah default filter 'Posisi Permohonan' untuk memilih semua ---
        selected_posisi = st.multiselect(
            'Pilih Posisi Permohonan:',
            options=posisi_options,
            default=posisi_options # Default memilih semua opsi yang ada
        )
            
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

        # --- PERUBAHAN 1: Tambahkan logika filter 'Jenis Produk' ke dalam penyaringan data ---
        filtered_df = df[
            (df['Tanggal Permohonan'] >= start_datetime) & (df['Tanggal Permohonan'] < end_datetime) &
            (df['Layanan'].isin(selected_layanan)) &
            (df['Kategori Produk'].isin(selected_kategori)) &
            (df['Jenis Produk'].isin(selected_jenis_produk)) & # <-- Logika filter baru
            (df['Posisi Permohonan'].isin(selected_posisi))
        ]

        st.header(f"Menampilkan {len(filtered_df)} Permohonan")
        # --- PERUBAHAN 2: Ubah teks deskripsi untuk aturan pewarnaan baru ---
        st.write("Permohonan > 3 hari ditandai hijau muda, dan > 30 hari ditandai hijau tua.")
        
        # --- PERUBAHAN 2: Gunakan fungsi highlight_by_age yang baru ---
        st.dataframe(
            filtered_df.style.apply(highlight_by_age, axis=1),
            use_container_width=True
        )

except FileNotFoundError:
    st.error("File 'data_imigrasi.csv' tidak ditemukan. Pastikan Anda sudah menjalankan 'scraper.py' terlebih dahulu.")
except Exception as e:
    st.error(f"Terjadi error saat memproses data: {e}")
