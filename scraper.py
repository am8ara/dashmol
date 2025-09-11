import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import os

# =============================================================================
# Konfigurasi
# =============================================================================
LOGIN_URL = 'https://admin-molina.imigrasi.go.id/admin/login'
DATA_URL = 'https://admin-molina.imigrasi.go.id/admin/verification-staypermit'
YOUR_USERNAME = os.getenv("MOLINA_USERNAME")
YOUR_PASSWORD = os.getenv("MOLINA_PASSWORD")

TABS_TO_SCRAPE = ["Verifikasi", "Ditolak", "Dipending", "Disetujui", "Terbit"]

TAB_ID_MAP = {
    "Verifikasi": "verifikasi", "Ditolak": "ditolak", "Dipending": "dipending",
    "Disetujui": "disetujui", "Terbit": "terbit"
}

# =============================================================================
# Script Otomatisasi
# =============================================================================
if not YOUR_USERNAME or not YOUR_PASSWORD:
    print("Error: Secret MOLINA_USERNAME dan MOLINA_PASSWORD belum diatur!")
    exit()

print("Memulai proses pengambilan data dari semua tab...")

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
except Exception:
    driver = webdriver.Chrome()

all_data_from_all_tabs = []

try:
    # --- Proses Login dan Navigasi ---
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(YOUR_USERNAME)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(YOUR_PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    print("Login berhasil.")
    driver.get(DATA_URL)
    print(f"Berhasil membuka halaman data utama: {driver.current_url}")
    time.sleep(3)

    # --- Loop Utama untuk Setiap Tab ---
    for tab_name in TABS_TO_SCRAPE:
        print(f"\n--- Memulai proses untuk tab: '{tab_name}' ---")
        try:
            tab_id_suffix = TAB_ID_MAP[tab_name]
            tab_id = f"data-{tab_id_suffix}-tab"
            tab_element = wait.until(EC.element_to_be_clickable((By.ID, tab_id)))
            tab_element.click()
            print(f"Berhasil mengklik tab '{tab_name}'.")
            wait.until(EC.text_to_be_present_in_element_attribute((By.ID, tab_id), 'class', 'active'))
            print("Tab dikonfirmasi aktif.")
            
            try:
                dropdown_id = f"{tab_id_suffix}-table_length"
                select_element = wait.until(EC.element_to_be_clickable((By.NAME, dropdown_id)))
                Select(select_element).select_by_value("100")
                print("Berhasil mengubah tampilan menjadi 100 data per halaman.")
                time.sleep(3)
            except TimeoutException:
                print("Dropdown 'Show Entries' tidak ditemukan, melanjutkan dengan default.")
            
            # --- Loop Pagination ---
            page_number = 1
            while True:
                try:
                    print(f"Membaca data dari Halaman {page_number} di tab '{tab_name}'...")
                    content_pane_id = f"data-{tab_id_suffix}"
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"#{content_pane_id} tbody tr")))
                    table_body = driver.find_element(By.CSS_SELECTOR, f"#{content_pane_id} tbody")
                    
                    rows = table_body.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) > 1:
                            row_data = [col.text for col in cols]
                            if row_data:
                                all_data_from_all_tabs.append(row_data)
                
                except StaleElementReferenceException:
                    print("Terdeteksi refresh halaman (stale element), mencoba membaca ulang halaman...")
                    continue 
                except TimeoutException:
                    print(f"Tab '{tab_name}' tidak memiliki data. Lanjut ke tab berikutnya.")
                    break
                
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

# --- 4. Proses Akhir ---
df = pd.DataFrame()
if all_data_from_all_tabs:
    print(f"\nTotal {len(all_data_from_all_tabs)} baris data berhasil dikumpulkan dari SEMUA tab.")
    
    # --- PASTIKAN BARIS INI TEPAT SEPERTI DI BAWAH INI ---
    # --- INI ADALAH SUMBER ERROR ANDA ---
    column_headers = ["Tanggal Pembayaran", "Layanan", "Kategori Produk", "Nomor Permohonan", "Tanggal Permohonan", "Penjamin", "Nama", "Jenis Kelamin", "Tanggal Lahir", "Kebangsaan", "No. Passport", "Jenis Produk", "Tujuan", "Posisi Permohonan", "Status Permohonan"]
    # ----------------------------------------------------

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