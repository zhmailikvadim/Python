import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Пути и значения
chromedriver_path = r"d:\Fiori\bot\chromedriver.exe"
totp_url = "https://totp.danhersam.com/"
target_url = "https://sappoint.ftp.sh:1443"
secret_key = "XB3G3GIAB5SJV7DLRBPBLVPVLOHBTLR5"
token_prefix = "243225"


def run():
    """Основная точка входа для бота"""
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-extensions')

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)


START_ID = 3736846
COUNT = 30
OUTPUT_DIR = "selenium_notes"
DELAY = 3  # секунды на загрузку страницы


def setup_driver():
    options = Options()
    options.add_argument("--headless")  # убрать окно браузера
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Если нужен реальный браузер с отображением, закомментируйте headless
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def download_note(driver, note_id):
    url = f"https://sappoint.ftp.sh:1443/#/Notes/{note_id}"
    print(f"Загрузка ID {note_id}...")
    driver.get(url)
    time.sleep(DELAY)  # ждём рендеринга
    page_source = driver.page_source
    filename = os.path.join(OUTPUT_DIR, f"note_{note_id}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(page_source)
    print(f"[OK] Сохранён {filename}")
    return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    driver = setup_driver()
    try:
        for i in range(COUNT):
            note_id = START_ID - i
            download_note(driver, note_id)
    finally:
        driver.quit()
    print("Готово.")


if __name__ == "__main__":
    main()