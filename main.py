from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urlparse

input_file = "logins.txt"
good_file = "good.txt"
output_file = "output.txt"
successful_identifier = "erfolgreicher_login"  # Ihr tatsächlicher Erfolgsindikator


def ensure_url_scheme(url):
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url  # Standardmäßig http hinzufügen
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
        file_handle.write(trimmed_message + '\n')  # Print to file


def process_login_selenium(driver, url, username, password, output_handle=None, good_handle=None):
    url = ensure_url_scheme(url)
    if not is_valid_url(url):
        log_output(f"Ungültige URL: {url}", output_handle)
        return

    try:
        log_output(f"Versuche, zu navigieren: {url}", output_handle)
        driver.get(url)
        log_output(f"Erfolgreich zu {url} navigiert", output_handle)
        wait = WebDriverWait(driver, 20)  # Wartezeit von 20 Sekunden

        # Cookie-Banner wegklicken, wenn vorhanden
        try:
            cookie_buttons = [
                (By.XPATH, "//button[text()='Accept']"),
                (By.XPATH, "//button[text()='I agree']"),
                (By.XPATH, "//button[contains(text(), 'ich stimme zu')]")
            ]
            for by, value in cookie_buttons:
                try:
                    cookie_button = wait.until(EC.element_to_be_clickable((by, value)))
                    cookie_button.click()
                    log_output(f"Cookie-Banner geklickt: {value}", output_handle)
                    break
                except Exception:
                    log_output(f"Kein Cookie-Banner für {value} gefunden", output_handle)

        except Exception as e:
            log_output(f"Kein Cookie-Banner gefunden oder Fehler beim Wegklicken: {e}", output_handle)

        # Finde Benutzername- und Passwort-Felder (angepasst an die Struktur der Seite)
        try:
            user_elem = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            pass_elem = wait.until(EC.presence_of_element_located((By.NAME, "password")))

            log_output(f"Benutzername- und Passwort-Felder auf {url} gefunden.", output_handle)
            user_elem.send_keys(username)
            pass_elem.send_keys(password)

            # Finde und klicke auf den Login-Button
            submit_elem = wait.until(EC.element_to_be_clickable(
                (By.NAME, "login_button_name_here")))  # Anpassen an die tatsächliche Struktur der Login-Seite
            submit_elem.click()
        except Exception as elem_error:
            log_output(f"Fehler beim Finden oder Ausfüllen der Login-Elemente auf {url}: {elem_error}", output_handle)
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


# Startzeit festhalten
start_time = time.time()

with open(good_file, "w") as good, open(output_file, "w") as output:
    with open(input_file, "r", encoding="ISO-8859-1") as file:
        lines_buffer = []

        # Selenium WebDriver initialisieren (Chrome über Homebrew installiert)
        options = webdriver.ChromeOptions()
        options.add_argument(
            '--user-agent=your_user_agent_string')  # Optional: anpassen, um einen speziellen Benutzeragent zu simulieren

        # Verwenden Sie einfach webdriver.Chrome(), da der ChromeDriver im PATH über Homebrew installiert ist
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

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

                    log_output(f"Verarbeite URL: {url} mit Benutzer: {username}", output)  # Debugging-Ausgabe
                    process_login_selenium(driver, url, username, password, output, good)
                    lines_buffer.clear()

            log_output("Alle Anfragen bearbeitet. Browserfenster bleibt zur Überprüfung offen.", output)
            input("Drücken Sie Enter, um das Skript zu beenden...")

        finally:
            driver.quit()

end_time = time.time()
execution_time = end_time - start_time
print(f"Die Laufzeit des Skripts beträgt {execution_time} Sekunden")