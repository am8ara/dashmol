import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# =============================================================================
# Konfigurasi (Pastikan sudah benar)
# =============================================================================
LOGIN_URL = 'https://admin-molina.imigrasi.go.id/admin/login' 
DATA_URL = 'https://admin-molina.imigrasi.go.id/admin/verification-staypermit' 
YOUR_USERNAME = os.getenv("MOLINA_USERNAME")
YOUR_PASSWORD = os.getenv("MOLINA_PASSWORD")

# Pastikan Anda memberi tahu jika secret tidak ditemukan
if not YOUR_USERNAME or not YOUR_PASSWORD:
    print("Error: Secret MOLINA_USERNAME dan MOLINA_PASSWORD belum diatur!")
    # Anda bisa memilih untuk menghentikan skrip di sini jika mau
    # exit() 
CHROMEDRIVER_PATH = './chromedriver.exe'

# =============================================================================
# Script Otomatisasi Final dengan Selector yang Benar
# =============================================================================
print("Memulai proses pengambilan data...")

service = Service(executable_path=CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# options.add_argument("--headless") # Aktifkan baris ini jika sudah berjalan lancar untuk menjalankannya di background
driver = webdriver.Chrome(service=service, options=options)

all_rows_data = []

try:
    # --- 1. Proses Login ---
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(YOUR_USERNAME)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(YOUR_PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    print("Login berhasil.")
    
    # --- 2. Buka Halaman Data ---
    driver.get(DATA_URL)
    print(f"Berhasil membuka halaman data: {driver.current_url}")

    # --- 3. Loop untuk Mengambil Semua Halaman ---
    page_number = 1
    while True:
        print(f"Membaca data dari Halaman {page_number}...")
        
        table_body = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-responsive tbody")))
        time.sleep(2) 
        
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text for col in cols if col.text.strip() != '']
            if row_data:
                all_rows_data.append(row_data)

        # --- Cek dan Klik Tombol "Next" (PERBAIKAN FINAL) ---
        try:
            # Cari link yang teksnya persis "Next"
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            
            # Cek apakah tombol nonaktif. Biasanya elemen induknya (<li>) punya class 'disabled'
            parent_li = next_button.find_element(By.XPATH, "..")
            if "disabled" in parent_li.get_attribute("class"):
                print("Tombol 'Next' nonaktif. Ini adalah halaman terakhir.")
                break 
            else:
                print("Menuju halaman berikutnya...")
                driver.execute_script("arguments[0].click();", next_button)
                page_number += 1
                time.sleep(2)

        except NoSuchElementException:
            print("Tombol 'Next' tidak ditemukan. Diasumsikan hanya ada satu halaman.")
            break 

except Exception as e:
    print(f"Terjadi error: {e}")

finally:
    driver.quit()

# --- 4. Buat DataFrame dan Simpan ke CSV ---
df = pd.DataFrame()
if all_rows_data:
    print(f"\nTotal {len(all_rows_data)} baris data berhasil dikumpulkan dari semua halaman.")
    column_headers = [
        "Tanggal Pembayaran", "Layanan", "Kategori Produk", "Nomor Permohonan",
        "Tanggal Permohonan", "Penjamin", "Nama", "Jenis Kelamin",
        "Tanggal Lahir", "Kebangsaan", "No. Passport", "Jenis Produk",
        "Tujuan", "Posisi Permohonan", "Status Permohonan"
    ]
    df = pd.DataFrame(all_rows_data, columns=column_headers)
    df.to_csv('data_imigrasi.csv', index=False)
    print(f"Data berhasil disimpan ke 'data_imigrasi.csv'.")
else:
    print("Gagal menyimpan file: Tidak ada data yang berhasil diekstrak.")

print("Proses selesai.")