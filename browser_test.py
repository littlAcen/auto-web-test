from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urlparse


def ensure_url_scheme(url):
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url
    return url


def log_output(message):
    trimmed_message = (message[:497] + '...') if len(message) > 500 else message
    print(trimmed_message)  # Print to console


# Testen Sie zunächst die grundlegende Browsernavigation
try:
    driver_path = '/usr/local/bin/chromedriver'  # Stellen Sie sicher, dass dieser Pfad korrekt ist
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=your_user_agent_string')  # Optional: Benutzeragent anpassen
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    # Testnavigation zu einer bekannten Seite
    driver.get('https://www.google.de')
    log_output("Navigiert zu 'https://www.google.de'")

    # Warten Sie eine Weile, um sicherzustellen, dass die Seite vollständig geladen ist
    time.sleep(5)

    driver.quit()
except Exception as e:
    log_output(f"Fehler beim Starten des Webdrivers oder der Navigation: {e}")
