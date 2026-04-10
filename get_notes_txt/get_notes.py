import time
import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pyotp  # для генерации TOTP

# ---------- НАСТРОЙКИ ----------
chromedriver_path = r"d:\Fiori\Python\chromedriver.exe"
target_url = "https://sappoint.ftp.sh:1443"
secret_key = "XB3G3GIAB5SJV7DLRBPBLVPVLOHBTLR5"
token_prefix = "243225"

START_ID = 3736846
OUTPUT_DIR = "sap_notes_clean"
TIMEOUT = 30
REQUIRED_KEYWORD = "Symptom"

PROCESSED_LOG = os.path.join(OUTPUT_DIR, "processed_ids.pkl")

def generate_totp():
    """Генерирует TOTP на основе секретного ключа"""
    totp = pyotp.TOTP(secret_key)
    token = totp.now()
    return token_prefix + token

def extract_note_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', class_='longText')
    if not content_div:
        content_div = soup.find('div', {'id': '__layout4'})
    if content_div:
        return str(content_div)
    return None

def is_valid_note(content_html):
    if not content_html:
        return False
    return REQUIRED_KEYWORD.lower() in content_html.lower()

def load_processed_ids():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'rb') as f:
            return pickle.load(f)
    return set()

def save_processed_ids(processed_set):
    with open(PROCESSED_LOG, 'wb') as f:
        pickle.dump(processed_set, f)

def cleanup_no_symptom_files():
    """Удаляет все файлы *_no_symptom.html, они больше не нужны"""
    for fname in os.listdir(OUTPUT_DIR):
        if fname.endswith("_no_symptom.html"):
            os.remove(os.path.join(OUTPUT_DIR, fname))
            print(f"Удалён старый файл: {fname}")

def download_note(driver, note_id):
    url = f"{target_url}/#/Notes/{note_id}"
    print(f"Обработка ID {note_id}...")
    driver.get(url)

    try:
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: len(d.find_element(By.TAG_NAME, "body").text.strip()) > 100
        )
    except Exception:
        print(f"  Таймаут загрузки для {note_id}")
        return False

    time.sleep(2)

    full_html = driver.page_source
    clean_content = extract_note_content(full_html)

    if not clean_content:
        # Нота не существует или не загрузилась – помечаем как обработанную (неудачно)
        print(f"  Не удалось извлечь содержимое для {note_id}")
        return False

    if is_valid_note(clean_content):
        filename = os.path.join(OUTPUT_DIR, f"note_{note_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_content)
        print(f"  ✅ Сохранена нота {note_id} (содержит {REQUIRED_KEYWORD})")
        return True
    else:
        # Нота есть, но нет Symptom – не сохраняем (просто помечаем обработанной)
        print(f"  ⚠️ Нота {note_id} не содержит '{REQUIRED_KEYWORD}' – пропущена")
        return False


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cleanup_no_symptom_files()          # удаляем старые заглушки
    processed = load_processed_ids()    # загружаем ID, которые уже обработаны

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-extensions')
    # Подавляем лишние логи
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # ----- АВТОРИЗАЦИЯ (без TOTP-сайта) -----
        print("🔐 Выполняем вход...")
        driver.get(target_url)
        driver.maximize_window()

        # Ждём появления полей логина
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginPage--userID-inner"))
        )
        login_field.send_keys("v.zhmajlik@beloil.by")
        password_field = driver.find_element(By.ID, "loginPage--userPassword-inner")
        password_field.send_keys("B4@$D!&y")
        token_field = driver.find_element(By.ID, "loginPage--totp-inner")
        token_field.clear()
        token_field.send_keys(generate_totp())
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#__button0-BDI-content"))
        )
        login_button.click()

        # Ждём, пока основное приложение загрузится
        time.sleep(10)

        # ----- ОСНОВНОЙ ЦИКЛ (от START_ID вниз до 1) -----
        note_id = START_ID
        while note_id >= 1:
            if note_id in processed:
                print(f"⏩ ID {note_id} уже обработан, пропускаем")
                note_id -= 1
                continue

            success = download_note(driver, note_id)
            # Добавляем ID в обработанные (независимо от успеха/неудачи)
            processed.add(note_id)
            save_processed_ids(processed)
            note_id -= 1
            time.sleep(1)

        print("🎉 Все ID от {} до 1 обработаны!".format(START_ID))

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        driver.save_screenshot('fatal_error.png')
    finally:
        driver.quit()


if __name__ == "__main__":
    run()
    