import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# ---------- НАСТРОЙКИ ----------
chromedriver_path = r"d:\Fiori\bot\chromedriver.exe"
totp_url = "https://totp.danhersam.com/"
target_url = "https://sappoint.ftp.sh:1443"
secret_key = "XB3G3GIAB5SJV7DLRBPBLVPVLOHBTLR5"
token_prefix = "243225"

START_ID = 3736846
OUTPUT_DIR = "sap_notes_clean"
TIMEOUT = 30
REQUIRED_KEYWORD = "Symptom"

def extract_note_content(html):
    """Извлекает содержимое ноты из HTML страницы портала"""
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', class_='longText')
    if not content_div:
        content_div = soup.find('div', {'id': '__layout4'})
    if content_div:
        return str(content_div)
    return None

def is_valid_note(content_html):
    """Проверяет, содержит ли HTML ноты слово Symptom"""
    if not content_html:
        return False
    return REQUIRED_KEYWORD.lower() in content_html.lower()

def is_note_already_downloaded(note_id):
    """Проверяет, существует ли уже файл (с любым суффиксом) для данного ID"""
    filename_clean = os.path.join(OUTPUT_DIR, f"note_{note_id}.html")
    filename_no_symptom = os.path.join(OUTPUT_DIR, f"note_{note_id}_no_symptom.html")
    return os.path.exists(filename_clean) or os.path.exists(filename_no_symptom)

def download_note(driver, note_id):
    """Загружает страницу, извлекает содержимое, проверяет Symptom и сохраняет с соответствующим именем"""
    url = f"{target_url}/#/Notes/{note_id}"
    print(f"Переход к ноте {note_id}...")
    driver.get(url)

    try:
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: len(d.find_element(By.TAG_NAME, "body").text.strip()) > 100
        )
    except Exception:
        print(f"  Таймаут загрузки страницы для {note_id}")
        return

    time.sleep(3)

    full_html = driver.page_source
    clean_content = extract_note_content(full_html)

    if not clean_content:
        print(f"  Не удалось извлечь содержимое для {note_id} (возможно, нота не существует)")
        # Всё равно сохраняем "пустой" файл с пометкой, чтобы не перекачивать
        filename = os.path.join(OUTPUT_DIR, f"note_{note_id}_no_symptom.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<!-- No content extracted for note {note_id} -->\n{full_html}")
        print(f"  Сохранён заглушка {filename}")
        return

    if is_valid_note(clean_content):
        filename = os.path.join(OUTPUT_DIR, f"note_{note_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_content)
        size = os.path.getsize(filename)
        print(f"  ✅ Сохранена нота {note_id} (содержит {REQUIRED_KEYWORD}) ({size} байт)")
    else:
        filename = os.path.join(OUTPUT_DIR, f"note_{note_id}_no_symptom.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_content)
        size = os.path.getsize(filename)
        print(f"  ⚠️ Нота {note_id} не содержит '{REQUIRED_KEYWORD}' – сохранена как {filename} ({size} байт)")

def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-extensions')

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # ---------- АВТОРИЗАЦИЯ ----------
        print("🔐 Выполняем вход...")
        driver.get(totp_url)
        driver.maximize_window()
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#app > div > div:nth-child(2) > div > input"))
        )
        input_field.clear()
        input_field.send_keys(secret_key)
        time.sleep(1)
        copy_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#clipboard-button > img"))
        )
        copy_button.click()
        time.sleep(1)
        token = driver.execute_script("return navigator.clipboard.readText();")
        full_token = token_prefix + token
        first_tab = driver.window_handles[0]
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(target_url)
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginPage--userID-inner"))
        )
        login_field.send_keys("v.zhmajlik@beloil.by")
        password_field = driver.find_element(By.ID, "loginPage--userPassword-inner")
        password_field.send_keys("B4@$D!&y")
        token_field = driver.find_element(By.ID, "loginPage--totp-inner")
        token_field.clear()
        token_field.send_keys(full_token)
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#__button0-BDI-content"))
        )
        login_button.click()
        driver.switch_to.window(first_tab)
        driver.close()
        time.sleep(10)
        driver.switch_to.window(driver.window_handles[0])

        # ---------- СКАЧИВАНИЕ НОТ ДО ID=1 ----------
        print(f"📥 Начинаем скачивание нот от {START_ID} до 1...")
        note_id = START_ID

        while note_id >= 1:
            if is_note_already_downloaded(note_id):
                print(f"⏩ Пропускаем ID {note_id} (уже обработан)")
                note_id -= 1
                continue

            download_note(driver, note_id)
            note_id -= 1
            time.sleep(1)

        print("🎉 Готово! Все ID обработаны до 1.")

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        driver.save_screenshot('fatal_error.png')
    finally:
        driver.quit()

if __name__ == "__main__":
    run()