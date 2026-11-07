import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

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

# Nederlandse maanden
maanden = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]

# =========================================================
# VANDAAG EN DE 10 DAGEN DIE WE WILLEN OPHALEN
# =========================================================

vandaag = datetime.now().date()

# 10 dagen inclusief vandaag
einddatum = vandaag + timedelta(days=9)

print(f"Vandaag: {vandaag}")
print(f"Getijden nodig van {vandaag} t/m {einddatum}")

# =========================================================
# BEPALEN WELKE MAANDEN NODIG ZIJN
# =========================================================

maanden_nodig = []

datum = vandaag

while datum <= einddatum:

    maand_jaar = (datum.year, datum.month)

    if maand_jaar not in maanden_nodig:
        maanden_nodig.append(maand_jaar)

    # Naar de eerste dag van de volgende maand
    if datum.month == 12:
        datum = datum.replace(
            year=datum.year + 1,
            month=1,
            day=1
        )
    else:
        datum = datum.replace(
            month=datum.month + 1,
            day=1
        )

print("Maanden die nodig zijn:")

for jaar, maand_nummer in maanden_nodig:
    print(f"- {maanden[maand_nummer - 1]} {jaar}")


# =========================================================
# KORTE MAANDNAMEN
# =========================================================

maand_namen_kort = [
    "jan",
    "feb",
    "mrt",
    "apr",
    "mei",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "dec"
]


# =========================================================
# DATUM UIT DE WEBSITE-TEKST HALEN
# =========================================================

def vind_datum(tekst, jaar):

    match = re.search(
        r'(\d{1,2})\s+'
        r'(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)',
        tekst.lower()
    )

    if not match:
        return None

    dag = int(match.group(1))
    maand_kort = match.group(2)

    try:

        maand_nummer = maand_namen_kort.index(
            maand_kort
        ) + 1

        return datetime(
            jaar,
            maand_nummer,
            dag
        ).date()

    except ValueError:
        return None


# =========================================================
# ALLE GETIJDEN VERZAMELEN - NIEUWE HTML-STructuur
# =========================================================

alle_dagen = []

for jaar, maand_nummer in maanden_nodig:

    maand = f"{maanden[maand_nummer - 1]} {jaar}"

    print()
    print(f"Zoeken naar: {maand}")

    kop = soup.find(
        'h2',
        string=lambda s:
        s and maand.lower() in s.lower()
    )

    if not kop:
        print(f"Kop {maand} niet gevonden!")
        continue

    print(f"Kop {maand} gevonden!")

    huidige_dag = None

    for element in kop.find_all_next():

        # Stop bij volgende maand
        if element.name == 'h2':
            break

        if (
            element.name != 'div'
            or 'row' not in element.get('class', [])
        ):
            continue

        # De vijf cellen ophalen
        cols = element.find_all(
            'div',
            recursive=False
        )

        if len(cols) < 5:
            continue

        # =================================================
        # CONTROLEREN OF DIT EEN NIEUWE DAG IS
        # =================================================

        dagcel = cols[0]

        if 'daycount' in dagcel.get('class', []):

            dagnaam_datum = dagcel.get_text(
                " ",
                strip=True
            )

            datum = vind_datum(
                dagnaam_datum,
                jaar
            )

            if datum:

                huidige_dag = {
                    "dag": dagnaam_datum,
                    "datum": datum,
                    "tijden": []
                }

                alle_dagen.append(huidige_dag)

        # Geen geldige huidige dag?
        if huidige_dag is None:
            continue

        # =================================================
        # HOOGWATER - KOLOM 2
        # =================================================

        hoogwater_uur = cols[1].get_text(
            " ",
            strip=True
        )

        hoogwater_match = re.search(
            r'(\d{1,2}[:.]\d{2})',
            hoogwater_uur
        )

        if hoogwater_match:

            tijd = hoogwater_match.group(1).replace('.', ':')

            tekst = f"{tijd} (hoogwater)"

            huidige_dag["tijden"].append(tekst)

        # =================================================
        # LAAGWATER - KOLOM 4
        # =================================================

        laagwater_uur = cols[3].get_text(
            " ",
            strip=True
        )

        laagwater_match = re.search(
            r'(\d{1,2}[:.]\d{2})',
            laagwater_uur
        )

        if laagwater_match:

            tijd = laagwater_match.group(1).replace('.', ':')

            tekst = f"{tijd} (laagwater)"

            huidige_dag["tijden"].append(tekst)


# =========================================================
# ALLEEN GELDIGE DATUMS HOUDEN
# =========================================================

alle_dagen = [
    dag
    for dag in alle_dagen
    if dag["datum"] is not None
]


# =========================================================
# DUBBELE DAGEN SAMENVOEGEN
# =========================================================

unieke_dagen = {}

for dag in alle_dagen:

    datum = dag["datum"]

    if datum not in unieke_dagen:

        unieke_dagen[datum] = dag

    else:

        unieke_dagen[datum]["tijden"].extend(
            dag["tijden"]
        )


# =========================================================
# GETIJDEN PER DAG SORTEREN
# =========================================================

for dag in alle_dagen:

    dag["tijden"].sort(
        key=lambda x:
        int(x.split(':')[0]) * 60
        + int(x.split(':')[1].split()[0])
    )


# =========================================================
# ALLEEN DE 10 DAGEN VANAF VANDAAG
# =========================================================

dag_data = [
    dag
    for dag in alle_dagen
    if vandaag <= dag["datum"] <= einddatum
]

# Sorteren op datum
dag_data.sort(
    key=lambda x: x["datum"]
)

# Maximaal 10 dagen
dag_data = dag_data[:10]


# =========================================================
# DATUM UIT DE JSON VERWIJDEREN
# =========================================================

for dag in dag_data:
    del dag["datum"]


# =========================================================
# CONTROLEREN HOEVEEL DAGEN GEVONDEN ZIJN
# =========================================================

print()
print("--------------------------------")
print(f"{len(dag_data)} dagen gevonden")
print("--------------------------------")

for dag in dag_data:
    print(dag["dag"])


# =========================================================
# GROEPEN VAN 10 DAGEN
# =========================================================

batches = [
    dag_data[i:i + 10]
    for i in range(0, len(dag_data), 10)
]


# =========================================================
# JSON-SLEUTEL
# =========================================================

if dag_data:

    maand_sleutel = (
        f"{maanden[vandaag.month - 1]} "
        f"{vandaag.year}"
    )

    result[maand_sleutel] = batches


# =========================================================
# JSON OPSLAAN
# =========================================================

with open(
    'data_tides.json',
    'w',
    encoding='utf-8'
) as f:

    json.dump(
        result,
        f,
        ensure_ascii=False,
        indent=2
    )


print()
print(
    f"Getijden van {len(dag_data)} dagen "
    f"opgeslagen in data_tides.json"
)




