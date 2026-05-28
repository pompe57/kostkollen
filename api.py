# api.py - All kommunikation med Livsmedelsverket

import os
import time
import json
import requests

FILNAMN = "data/livsmedel_data.json"
MAX_ALDER_SEKUNDER = 24 * 60 * 60  # 24 timmar
API_BASE = "https://dataportal.livsmedelsverket.se/livsmedel/api/v1"
HEADERS = {'User-Agent': 'KostKollen/1.0'}

def uppdatera_lokal_data():
    """Hämtar färsk data från API:et och sparar till filen."""
    url = f"{API_BASE}/livsmedel?limit=2575"
    print("Hämtar ny data från Livsmedelsverket...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        livsmedel_lista = data if isinstance(data, list) else data.get('livsmedel', [])
        os.makedirs("data", exist_ok=True)
        with open(FILNAMN, "w", encoding="utf-8") as f:
            json.dump(livsmedel_lista, f, ensure_ascii=False, indent=4)
        print("Lokala filen har uppdaterats!")
        return livsmedel_lista
    except Exception as e:
        print(f"Kunde inte uppdatera från API:et ({e}).")
        if os.path.exists(FILNAMN):
            print("Använder befintlig lokal fil.")
            with open(FILNAMN, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def hamta_alla_livsmedel():
    """Returnerar livsmedelsdata, från fil eller API."""
    if not os.path.exists(FILNAMN):
        return uppdatera_lokal_data()
    fil_alder = time.time() - os.path.getmtime(FILNAMN)
    if fil_alder > MAX_ALDER_SEKUNDER:
        print("Lokala filen är äldre än 24 timmar.")
        return uppdatera_lokal_data()
    else:
        print("Använder sparad lokal data.")
        with open(FILNAMN, "r", encoding="utf-8") as f:
            return json.load(f)

def hamta_naringsvarden(nummer):
    """Hämtar alla näringsvärden för ett livsmedel via API:et."""
    url = f"{API_BASE}/livsmedel/{nummer}/naringsvarden"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Kunde inte hämta näringsvärden ({e}).")
        return []

def hamta_kalorier(nummer):
    """Returnerar kcal per 100g för ett livsmedel."""
    naringsvarden = hamta_naringsvarden(nummer)
    for n in naringsvarden:
        if n['namn'] == 'Energi (kcal)':
            return n['varde']
    return None