from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# URL и значения
totp_url = "https://totp.danhersam.com/"
target_url = "https://195.16.55.106/login"
secret_key = "XB3G3GIAB5SJV7DLRBPBLVPVLOHBTLR5"
token_prefix = "243225"

# Настройка опций Chrome
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--use-fake-ui-for-media-stream')
chrome_options.add_argument('--use-fake-device-for-media-stream')
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.clipboard_read": 1,
    "profile.default_content_setting_values.clipboard_write": 1,
    "profile.content_settings.exceptions.clipboard": {
        "https://totp.danhersam.com,*": {
            "last_modified": "13203264983197813",
            "setting": 1
        }
    }
})

# Настройка драйвера Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Первая вкладка - генерация токена
    driver.get(totp_url)
    driver.maximize_window()
    
    # Ввод секретного ключа
    input_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#app > div > div:nth-child(2) > div > input"))
    )
    input_field.clear()
    input_field.send_keys(secret_key)
    time.sleep(1)
    
    # Копирование токена
    copy_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#clipboard-button > img"))
    )
    copy_button.click()
    time.sleep(1)
    
    # Получаем токен из буфера обмена
    token = driver.execute_script("return navigator.clipboard.readText();")
    full_token = token_prefix + token
    
    # Сохраняем идентификатор первой вкладки
    first_tab = driver.window_handles[0]
    
    # Открываем новую вкладку
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    
    # Вторая вкладка - целевой сайт
    driver.get(target_url)
    
    # Ввод данных
    login_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "loginPage--userID-inner"))
    )
    login_field.send_keys("v.zhmajlik@beloil.by")
    
    password_field = driver.find_element(By.ID, "loginPage--userPassword-inner")
    password_field.send_keys("B4@$D!&y")
    
    # Ввод токена
    token_field = driver.find_element(By.ID, "loginPage--totp-inner")
    token_field.clear()
    token_field.send_keys(full_token)
    
    # Нажатие кнопки входа
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#__button0-BDI-content"))
    )
    login_button.click()
    
    # Закрываем первую вкладку
    driver.switch_to.window(first_tab)
    driver.close()
    time.sleep(10)
    
    # Переключаемся обратно на основную вкладку
    driver.switch_to.window(driver.window_handles[0])

except Exception as e:
    print(f"Произошла ошибка: {e}")
    driver.save_screenshot('error.png')

finally:
   pass
