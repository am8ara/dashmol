import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os

# =============================================================================
# Konfigurasi
# =============================================================================
LOGIN_URL = 'https://admin-molina.imigrasi.go.id/admin/login'
DATA_URL = 'https://admin-molina.imigrasi.go.id/admin/verification-staypermit'
YOUR_USERNAME = os.getenv("MOLINA_USERNAME")
YOUR_PASSWORD = os.getenv("MOLINA_PASSWORD")

TABS_TO_SCRAPE = ["Verifikasi", "Ditolak", "Dipending", "Disetujui", "Terbit"]

# =============================================================================
# Script Otomatisasi
# =============================================================================
if not YOUR_USERNAME or not YOUR_PASSWORD:
    print("Error: Secret MOLINA_USERNAME dan MOLINA_PASSWORD belum diatur di GitHub Actions!")
    exit()

print("Memulai proses pengambilan data dari semua tab...")

try:
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
except Exception:
    driver = webdriver.Chrome()

all_data_from_all_tabs = []

try:
    # --- 1. Proses Login ---
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(YOUR_USERNAME)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(YOUR_PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    print("Login berhasil.")

    # --- 2. Buka Halaman Data Utama ---
    driver.get(DATA_URL)
    print(f"Berhasil membuka halaman data utama: {driver.current_url}")
    time.sleep(3)

    # --- 3. Loop Utama untuk Setiap Tab ---
    for i, tab_name in enumerate(TABS_TO_SCRAPE):
        print(f"\n--- Memulai proses untuk tab: '{tab_name}' ---")
        try:
            # Ambil referensi ke badan tabel SAAT INI sebelum melakukan klik
            current_table_body = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-responsive tbody")))
            
            # Klik tab
            tab_element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, tab_name)))
            
            # Untuk tab pertama, kita tidak perlu menunggu 'staleness', langsung proses
            if i > 0: # Hanya lakukan klik jika bukan tab pertama (karena sudah aktif)
                 tab_element.click()
                 # --- PERINTAH TUNGGU BARU YANG LEBIH ANDAL ---
                 print("Menunggu data lama menghilang (staleness)...")
                 wait.until(EC.staleness_of(current_table_body))
                 print("Data baru terdeteksi. Memulai pengambilan.")
                 # ----------------------------------------------

            # --- Loop Pagination (untuk setiap halaman di dalam tab) ---
            page_number = 1
            while True:
                print(f"Membaca data dari Halaman {page_number} di tab '{tab_name}'...")
                
                # Selalu cari referensi baru ke badan tabel di setiap halaman
                table_body = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-responsive tbody")))
                
                # Tunggu hingga setidaknya satu baris muncul, untuk menghindari tabel kosong sesaat
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table-responsive tbody tr")))
                time.sleep(1) # Jeda singkat untuk render
                
                rows = table_body.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) > 1: # Mengabaikan baris "No data available in table"
                        row_data = [col.text for col in cols if col.text.strip() != '']
                        if row_data:
                            all_data_from_all_tabs.append(row_data)

                # Cek dan klik tombol 'Next'
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "Next")
                    parent_li = next_button.find_element(By.XPATH, "..")
                    if "disabled" in parent_li.get_attribute("class"):
                        print(f"Halaman terakhir di tab '{tab_name}' tercapai.")
                        break
                    else:
                        print("Menuju halaman berikutnya...")
                        driver.execute_script("arguments[0].click();", next_button)
                        page_number += 1
                        time.sleep(2)
                except NoSuchElementException:
                    print(f"Tidak ada halaman berikutnya di tab '{tab_name}'.")
                    break
        
        except TimeoutException:
            print(f"Gagal menemukan atau memproses tab '{tab_name}'. Melewati tab ini.")
            continue

except Exception as e:
    print(f"Terjadi error: {e}")

finally:
    driver.quit()

# --- 4. Buat DataFrame, Hapus Duplikat, dan Simpan ke CSV ---
# (Bagian ini tidak berubah)
df = pd.DataFrame()
if all_data_from_all_tabs:
    print(f"\nTotal {len(all_data_from_all_tabs)} baris data berhasil dikumpulkan dari SEMUA tab.")
    column_headers = ["Tanggal Pembayaran", "Layanan", "Kategori Produk", "Nomor Permohonan", "Tanggal Permohonan", "Penjamin", "Nama", "Jenis Kelamin", "Tanggal Lahir", "Kebangsaan", "No. Passport", "Jenis Produk", "Tujuan", "Posisi Permohonan", "Status Permohonan"]
    df = pd.DataFrame(all_data_from_all_tabs, columns=column_headers)
    
    initial_rows = len(df)
    df.drop_duplicates(subset=['Nomor Permohonan'], keep='last', inplace=True)
    final_rows = len(df)
    print(f"Menghapus {initial_rows - final_rows} data duplikat berdasarkan 'Nomor Permohonan'.")
    
    df.to_csv('data_imigrasi.csv', index=False)
    print(f"Data bersih sebanyak {final_rows} baris berhasil disimpan ke 'data_imigrasi.csv'.")
else:
    print("Gagal menyimpan file: Tidak ada data yang berhasil diekstrak.")

print("Proses selesai.")
