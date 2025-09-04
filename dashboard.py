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

st.title('📊 Dashboard Rekapitulasi Data Permohonan')
st.write('Dashboard ini digunakan untuk memantau status permohonan yang masuk.')

# =============================================================================
# Fungsi Bantuan (Helper Functions)
# =============================================================================

def hitung_hari_kerja(tanggal_awal):
    if pd.isna(tanggal_awal):
        return 0
    tanggal_akhir = pd.Timestamp.now().normalize()
    # np.busday_count menghitung hari kerja (Senin-Jumat)
    return np.busday_count(tanggal_awal.date(), tanggal_akhir.date())

def highlight_lebih_3_hari(row):
    tanggal_permohonan = row['Tanggal Permohonan']
    if pd.isna(tanggal_permohonan):
        return [''] * len(row)
    
    selisih = hitung_hari_kerja(tanggal_permohonan)
    
    if selisih > 3:
        # Memberikan style background warna merah muda
        return ['background-color: #FFCDD2'] * len(row)
    else:
        return [''] * len(row)

# =============================================================================
# Logika Utama Aplikasi
# =============================================================================

try:
    # Membaca data dari CSV yang sudah dibuat oleh scraper.py
    df = pd.read_csv('data_imigrasi.csv', encoding='utf-8')
    
    # --- Pembersihan dan Persiapan Data ---
    
    jumlah_baris_asli = len(df)
    
    # Mengubah 'Tanggal Permohonan' menjadi format datetime, mengabaikan error
    df['Tanggal Permohonan'] = pd.to_datetime(df['Tanggal Permohonan'], errors='coerce')

    # Menghapus baris jika 'Tanggal Permohonan' tidak valid
    df.dropna(subset=['Tanggal Permohonan'], inplace=True)
    
    jumlah_baris_bersih = len(df)
    if jumlah_baris_asli > jumlah_baris_bersih:
        st.warning(f"Peringatan: {jumlah_baris_asli - jumlah_baris_bersih} baris data diabaikan karena kolom tanggal kosong atau formatnya tidak dikenali.")

    if df.empty:
        st.error("Tidak ada data valid yang bisa ditampilkan. Mohon jalankan 'scraper.py' terlebih dahulu atau periksa isi file CSV Anda.")
    else:
        # Menambahkan kolom 'Lama Proses (Hari Kerja)'
        df['Lama Proses (Hari Kerja)'] = df['Tanggal Permohonan'].apply(hitung_hari_kerja)

        # =========================================================================
        # Tampilan Antarmuka (User Interface) - DENGAN FILTER BARU
        # =========================================================================
        
        st.header('Filter Data Permohonan')
        
        # --- Filter Berdasarkan Rentang Tanggal ---
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Dari Tanggal", 
                df['Tanggal Permohonan'].min().date()
            )
        with col2:
            end_date = st.date_input(
                "Sampai Tanggal", 
                datetime.now().date()
            )

        # --- FILTER BARU UNTUK LAYANAN DAN KATEGORI PRODUK ---
        # Ambil opsi unik dari kolom yang relevan
        layanan_options = df['Layanan'].unique()
        kategori_options = df['Kategori Produk'].unique()

        col3, col4 = st.columns(2)
        with col3:
            selected_layanan = st.multiselect(
                'Pilih Layanan:',
                options=layanan_options,
                default=layanan_options # Defaultnya memilih semua opsi
            )
        with col4:
            selected_kategori = st.multiselect(
                'Pilih Kategori Produk:',
                options=kategori_options,
                default=kategori_options # Defaultnya memilih semua opsi
            )
            
        # --- Logika untuk menerapkan semua filter ---
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

        # Terapkan semua filter secara berurutan
        filtered_df = df[
            # Filter Tanggal
            (df['Tanggal Permohonan'] >= start_datetime) & (df['Tanggal Permohonan'] < end_datetime) &
            # Filter Layanan
            (df['Layanan'].isin(selected_layanan)) &
            # Filter Kategori Produk
            (df['Kategori Produk'].isin(selected_kategori))
        ]

        st.header(f"Menampilkan {len(filtered_df)} Permohonan")
        st.write("Permohonan yang diproses lebih dari 3 hari kerja akan ditandai dengan warna merah muda.")
        
        # Tampilkan DataFrame dengan highlight
        st.dataframe(
            filtered_df.style.apply(highlight_lebih_3_hari, axis=1),
            use_container_width=True
        )

except FileNotFoundError:
    st.error("File 'data_imigrasi.csv' tidak ditemukan. Pastikan Anda sudah menjalankan 'scraper.py' untuk mengambil data terlebih dahulu.")
except Exception as e:
    st.error(f"Terjadi error saat memproses data: {e}")