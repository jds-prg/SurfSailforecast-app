import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

URL = 'https://blankenberge.com/nl/getijden-eb-vloed.php'

try:
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    print("Website getijden actief")
except requests.exceptions.RequestException:
    print("Website getijden inactief")
    exit()

soup = BeautifulSoup(resp.text, 'html.parser')
result = {}

# Maanden die je wilt , neemt de datum van de computer over

maanden = ["januari", "februari", "maart", "april", "mei", "juni","juli", "augustus", "september", "oktober", "november", "december"]


nu = datetime.now()
sleutel = f"{maanden[nu.month - 1]} {nu.year}"

maand = sleutel  # geen lijst nodig

kop = soup.find('h2', string=lambda s: s and maand.lower() in s.lower())

if not kop:
    print(f"Kop {maand} niet gevonden!")
else:
    print(f"Kop {maand} gevonden!")

    # Elke dag staat in een div met class 'row'
    div = kop.find_next('div')
    rows = div.find_all('div', class_='row') if div else []

    dag_data = []

    for row in rows:
        cols = [c.get_text(" ", strip=True)
                for c in row.find_all('div', recursive=False)]
        if len(cols) < 3:
            continue

        dagnaam_datum = cols[0]

        hoogwater_matches = re.findall(
            r'(\d{1,2}[:.]\d{2})\s*uur\s*(\d+,\d+)?', cols[1])
        laagwater_matches = re.findall(
            r'(\d{1,2}[:.]\d{2})\s*uur\s*(\d+,\d+)?', cols[2])

        tides = []

        for t, h in hoogwater_matches:
            s = f"{t} (hoogwater)"
            if h:
                s += f" {h}m"
            tides.append(s)

        for t, h in laagwater_matches:
            s = f"{t} (laagwater)"
            if h:
                s += f" {h}m"
            tides.append(s)

        tides.sort(key=lambda x: int(
            x.split(':')[0])*60 + int(x.split(':')[1].split()[0]))

        dag_data.append({
            "dag": dagnaam_datum,
            "tijden": tides
        })

    batches = [dag_data[i:i + 3] for i in range(0, len(dag_data), 3)]
    print(f"{len(dag_data)} dagen gevonden")
    result[maand] = batches

# Opslaan in JSON
with open('data_tides.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Getijden in batches van 3 dagen opgeslagen in data_tides.json")



