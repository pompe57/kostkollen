# recept.py - Recepthantering

import json
import os
from api import hamta_naringsvarden
from naringsvarden import (
    filtrera_naringsvarden,
    skala_naringsvarden,
    summera_naringsvarden,
    visa_naringsvarden,
    hamta_valda_naringsvarden,
)

RECEPT_FIL = "data/recept.json"

# Densitetstabell för volym -> gram (g per dl)
DENSITET = {
    "soppa":     100,
    "mjölk":     103,
    "grädde":    100,
    "juice":     104,
    "olja":       92,
    "standard":  100,   # default: 1 dl = 100g
}


# ============================================================
# FILHANTERING
# ============================================================

def ladda_recept():
    """Laddar receptdatabasen från fil."""
    if not os.path.exists(RECEPT_FIL):
        return {}
    with open(RECEPT_FIL, "r", encoding="utf-8") as f:
        return json.load(f)

def spara_recept_fil(recept):
    """Sparar receptdatabasen till fil."""
    os.makedirs("data", exist_ok=True)
    with open(RECEPT_FIL, "w", encoding="utf-8") as f:
        json.dump(recept, f, ensure_ascii=False, indent=4)


# ============================================================
# PORTIONSBERÄKNING – vikt eller volym
# ============================================================

def fraga_tillagad_mangd():
    """
    Frågar användaren om tillagad mängd i gram eller volym.
    Returnerar (gram_totalt, enhet_str).
    """
    print("\nAnge tillagad mängd:")
    print("  1. Vikt (gram)  [default]")
    print("  2. Volym (dl)")
    val = input("Välj (1/2): ").strip()

    if val == "2":
        dl = input("Tillagad volym (dl): ").strip()
        try:
            dl = float(dl)
        except ValueError:
            print("Ogiltigt värde, använder 0.")
            return 0, "dl"

        print("Välj densitet:")
        for i, (typ, täthet) in enumerate(DENSITET.items()):
            print(f"  {i+1}. {typ} ({täthet} g/dl)")
        val2 = input("Välj (Enter = standard): ").strip()
        try:
            vald_densitet = list(DENSITET.values())[int(val2) - 1]
            vald_typ = list(DENSITET.keys())[int(val2) - 1]
        except (ValueError, IndexError):
            vald_densitet = DENSITET["standard"]
            vald_typ = "standard"

        gram_totalt = dl * vald_densitet
        return gram_totalt, f"{dl:.1f} dl ({vald_typ})"
    else:
        gram = input("Tillagad vikt (gram): ").strip()
        try:
            gram = float(gram)
        except ValueError:
            print("Ogiltigt värde, använder 0.")
            return 0, "g"
        return gram, "g"


# ============================================================
# NÄRINGSBERÄKNING FÖR RECEPT
# ============================================================

def berakna_recept_naringsvarden(ingredienser):
    """
    Hämtar och summerar näringsvärden för alla ingredienser.
    Returnerar en summerad näringsvärdelista (per total receptvikt).
    """
    naringsvarden_per_ingrediens = []
    for ing in ingredienser:
        alla = hamta_naringsvarden(ing['nummer'])
        filtrerade = filtrera_naringsvarden(alla)
        skalade = skala_naringsvarden(filtrerade, ing['gram'])
        naringsvarden_per_ingrediens.append(skalade)
    return summera_naringsvarden(naringsvarden_per_ingrediens)

def skala_till_portion(naringsvarden_totalt, tillagad_gram, gram_per_portion):
    """Skalar totala näringsvärden till en portions grammatur."""
    if tillagad_gram <= 0:
        return naringsvarden_totalt
    faktor = gram_per_portion / tillagad_gram
    skalade = []
    for n in naringsvarden_totalt:
        skalat = dict(n)
        if n.get('varde') is not None:
            skalat['varde'] = n['varde'] * faktor
        skalade.append(skalat)
    return skalade

def naringsvarden_till_dict(naringsvarden_lista):
    """Konverterar näringsvärdelista till dict för lagring i JSON."""
    return {
        n['namn']: {'varde': n.get('varde'), 'enhet': n.get('enhet', '')}
        for n in naringsvarden_lista
    }

def naringsvarden_fran_dict(naringsvarden_dict):
    """Konverterar sparad dict tillbaka till näringsvärdelista."""
    return [
        {'namn': namn, 'varde': v['varde'], 'enhet': v['enhet']}
        for namn, v in naringsvarden_dict.items()
    ]


# ============================================================
# CRUD – skapa, visa, lista, ta bort recept
# ============================================================

def skapa_recept(namn, ingredienser, tillagad_gram, tillagad_enhet, portioner):
    """Skapar ett nytt recept, beräknar näringsvärden och sparar."""
    print("\nBeräknar näringsvärden för ingredienserna...")
    naringsvarden_totalt = berakna_recept_naringsvarden(ingredienser)

    gram_per_portion = tillagad_gram / portioner if portioner > 0 else 0
    naringsvarden_portion = skala_till_portion(
        naringsvarden_totalt, tillagad_gram, gram_per_portion
    )

    # Hämta kcal för summering
    kcal_totalt = next(
        (n['varde'] for n in naringsvarden_totalt if n['namn'] == 'Energi (kcal)'), 0
    )

    recept = ladda_recept()
    recept[namn] = {
        'namn': namn,
        'ingredienser': ingredienser,
        'tillagad_gram': tillagad_gram,
        'tillagad_enhet': tillagad_enhet,
        'portioner': portioner,
        'gram_per_portion': gram_per_portion,
        'kcal_totalt': kcal_totalt,
        'kcal_per_portion': kcal_totalt / portioner if portioner > 0 else 0,
        'naringsvarden_totalt': naringsvarden_till_dict(naringsvarden_totalt),
        'naringsvarden_per_portion': naringsvarden_till_dict(naringsvarden_portion),
    }
    spara_recept_fil(recept)

    print(f"\nRecept '{namn}' sparat!")
    print(f"Tillagad mängd : {tillagad_gram:.0f}g")
    print(f"Portioner      : {portioner}")
    print(f"Per portion    : {gram_per_portion:.0f}g  |  {kcal_totalt/portioner:.0f} kcal")
    return recept[namn]

def visa_recept(namn):
    """Visar ett sparat recept med näringsprofil per portion."""
    recept = ladda_recept()
    if namn not in recept:
        print(f"\nReceptet '{namn}' hittades inte.")
        return
    r = recept[namn]

    print(f"\n{'='*40}")
    print(f"  {r['namn']}")
    print(f"{'='*40}")
    print(f"  Tillagad mängd : {r['tillagad_gram']:.0f}g  ({r['tillagad_enhet']})")
    print(f"  Portioner      : {r['portioner']}")
    print(f"  Per portion    : {r['gram_per_portion']:.0f}g")

    print(f"\n  Ingredienser:")
    for ing in r['ingredienser']:
        print(f"    {ing['namn']:<30} {ing['gram']:>6.0f}g")

    # Näringsvärden per portion
    nv_lista = naringsvarden_fran_dict(r['naringsvarden_per_portion'])
    visa_naringsvarden(nv_lista, rubrik="Näringsvärden per portion", gram=r['gram_per_portion'])

    # Näringsvärden totalt
    nv_totalt = naringsvarden_fran_dict(r['naringsvarden_totalt'])
    visa_naringsvarden(nv_totalt, rubrik=f"Näringsvärden totalt ({r['tillagad_gram']:.0f}g)")

def lista_recept():
    """Listar alla sparade recept."""
    recept = ladda_recept()
    if not recept:
        print("\nInga recept sparade ännu.")
        return
    print("\n=== Sparade recept ===")
    for i, (namn, r) in enumerate(recept.items()):
        print(f"  {i+1}. {namn:<30} {r['kcal_per_portion']:.0f} kcal/portion  ({r['portioner']} port.)")

def ta_bort_recept(namn):
    """Tar bort ett recept från databasen."""
    recept = ladda_recept()
    if namn not in recept:
        print(f"\nReceptet '{namn}' hittades inte.")
        return
    del recept[namn]
    spara_recept_fil(recept)
    print(f"\nReceptet '{namn}' borttaget.")


# ============================================================
# PORTIONSBERÄKNING – beräkna om sparad recept
# ============================================================

def berakna_annan_portion(namn):
    """
    Låter användaren beräkna näringsvärden för valfri
    grammatur av ett sparat recept.
    """
    recept = ladda_recept()
    if namn not in recept:
        print(f"\nReceptet '{namn}' hittades inte.")
        return
    r = recept[namn]

    print(f"\nRecept: {r['namn']}  (standard: {r['gram_per_portion']:.0f}g/portion)")
    gram = input("Ange önskad grammatur (g): ").strip()
    try:
        gram = float(gram)
    except ValueError:
        print("Ogiltigt värde.")
        return

    nv_totalt = naringsvarden_fran_dict(r['naringsvarden_totalt'])
    nv_skalat = skala_till_portion(nv_totalt, r['tillagad_gram'], gram)
    visa_naringsvarden(nv_skalat, rubrik=f"{r['namn']} – {gram:.0f}g", gram=gram)