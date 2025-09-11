import requests
from bs4 import BeautifulSoup
import json
import re

URL = 'https://blankenberge.com/nl/getijden-eb-vloed.php'
resp = requests.get(URL)
soup = BeautifulSoup(resp.text, 'html.parser')

maanden = ['juli 2025', 'augustus 2025', 'september 2025']
result = {}

for maand in maanden:
    kop = soup.find('h2', string=lambda s: s and maand in s.lower())
    if not kop:
        print(f"Kop {maand} niet gevonden!")
        continue

    div = kop.find_next_sibling('div')
    if not div:
        print(f"Getijden div niet gevonden na kop {maand}!")
        continue

    tekst = div.get_text(separator=' ', strip=True)
    tekst = tekst.replace("Hoogwater Laagwater", "").strip()

    # Split per dag op afkortingen zoals "ma.", "di.", etc.
    dagen = re.split(r'(?=\b[a-z]{2}\.)', tekst)

    dag_data = []
    for dag in dagen:
        dag = dag.strip()
        if not dag:
            continue

        # Haal dagnaam en datum eruit
        m = re.match(r'^([a-z]{2}\.\s+[a-z]+\s+\d+\s+[a-z]+(?:\s+\d{1,2})?)\s+(.*)', dag)
        if m:
            dagnaam_datum = m.group(1)
            rest = m.group(2)
        else:
            dagnaam_datum = ''
            rest = dag

        # Pak alle tijden (bv '04:39 uur' of '04:39 uur' want soms is er een non-breaking space)
        tijden = re.findall(r'\d{1,2}[:.]?\d{2}\s*uur', rest)

        labels = ['Hoogwater', 'Laagwater', 'Hoogwater', 'Laagwater']

        tijden_met_labels = []
        for i, tijd in enumerate(tijden):
            label = labels[i] if i < len(labels) else ''
            tijden_met_labels.append(f"{tijd} ({label})")

        dag_data.append({
            "dag": dagnaam_datum,
            "tijden": tijden_met_labels
        })

    result[maand] = dag_data

with open('data_tides.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Getijden netjes opgeslagen in data_tides.json")
