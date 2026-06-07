# fardigratter.py - Hantering av färdigrätter

import json
import os
from api import hamta_naringsvarden, hamta_alla_livsmedel
from naringsvarden import (
    filtrera_naringsvarden,
    skala_naringsvarden,
    visa_naringsvarden,
)

CUSTOM_FIL = "data/fardigratter_custom.json"


# ============================================================
# FILHANTERING – egna/editerade färdigrätter
# ============================================================

def ladda_custom():
    """Laddar egna och editerade färdigrätter från fil."""
    if not os.path.exists(CUSTOM_FIL):
        return {}
    with open(CUSTOM_FIL, "r", encoding="utf-8") as f:
        return json.load(f)

def spara_custom(custom):
    """Sparar egna och editerade färdigrätter till fil."""
    os.makedirs("data", exist_ok=True)
    with open(CUSTOM_FIL, "w", encoding="utf-8") as f:
        json.dump(custom, f, ensure_ascii=False, indent=4)


# ============================================================
# SÖKNING – kombinerar API-data och egna tillägg
# ============================================================

def hamta_fardigratter():
    """
    Returnerar alla färdigrätter – Beräknade från API plus egna tillägg.
    Egna tillägg och redigeringar har företräde över API-data.
    """
    alla = hamta_alla_livsmedel()
    fran_api = [l for l in alla if l.get('livsmedelsTyp') == 'Beräknat']

    custom = ladda_custom()

    # Bygg kombinerad lista – custom har företräde
    api_index = {l['nummer']: l for l in fran_api}
    for nummer_str, data in custom.items():
        nummer = int(nummer_str)
        api_index[nummer] = data

    return list(api_index.values())

def sok_fardigratter(sokterm):
    """Söker bland färdigrätter på namn."""
    alla = hamta_fardigratter()
    sokterm = sokterm.lower()
    return [l for l in alla if sokterm in l['namn'].lower()]


# ============================================================
# VISNING
# ============================================================

def visa_sokresultat_fardigratter(resultat):
    """Skriver ut sökresultat med index och typ."""
    if not resultat:
        print("Inga träffar.")
        return
    for i, l in enumerate(resultat):
        typ = "(egen)" if l.get('livsmedelsTypId') == 99 else ""
        metod = l.get('tillagningsmetod', '')
        metod_str = f"  [{metod}]" if metod else ""
        print(f"  {i+1}. {l['namn']}{metod_str} {typ}")

def visa_fardigrat(livsmedel, gram=100):
    """
    Visar näringsprofil för en färdigrätt.
    Standard per 100g, eller per angiven grammatur.
    """
    nummer = livsmedel['nummer']
    namn = livsmedel['namn']

    alla_nv = hamta_naringsvarden(nummer)
    if not alla_nv:
        print(f"Kunde inte hämta näringsvärden för '{namn}'.")
        return

    filtrerade = filtrera_naringsvarden(alla_nv)

    if gram != 100:
        skalade = skala_naringsvarden(filtrerade, gram)
        visa_naringsvarden(skalade, rubrik=f"{namn}", gram=gram)
    else:
        visa_naringsvarden(filtrerade, rubrik=f"{namn} (per 100g)")

    # Visa råvaror om de finns
    _visa_ravaror(nummer)

def _visa_ravaror(nummer):
    """Visar råvarusammansättning för en beräknad rätt."""
    import requests
    from api import API_BASE, HEADERS
    try:
        r = requests.get(f"{API_BASE}/livsmedel/{nummer}/ravaror",
                         headers=HEADERS, timeout=10)
        ravaror = r.json()
        if ravaror:
            print(f"\n  Innehåller (råvaror):")
            for rv in ravaror:
                if rv['namn'] != 'Övrigt':
                    print(f"    {rv['namn']:<30} {rv['andel']:>4}%  [{rv['tillagning']}]")
    except Exception:
        pass


# ============================================================
# VÄLJ FÄRDIGRÄTT – interaktivt
# ============================================================

def valj_fardigrat(resultat):
    """Låter användaren välja en färdigrätt från listan."""
    if not resultat:
        return None
    val = input("\nVälj nummer (eller Enter för att avbryta): ").strip()
    if val == "":
        return None
    try:
        return resultat[int(val) - 1]
    except (ValueError, IndexError):
        print("Ogiltigt val.")
        return None


# ============================================================
# EDITERING – ändra näringsvärden på befintlig rätt
# ============================================================

def editera_fardigrat(livsmedel):
    """
    Låter användaren överskriva näringsvärden för en rätt.
    Sparas lokalt i fardigratter_custom.json.
    """
    nummer = livsmedel['nummer']
    namn = livsmedel['namn']

    print(f"\n=== Editera: {namn} ===")
    print("Hämtar aktuella näringsvärden...")

    alla_nv = hamta_naringsvarden(nummer)
    if not alla_nv:
        print("Kunde inte hämta näringsvärden.")
        return

    # Visa nuvarande värden med index
    print("\nNuvarande näringsvärden (per 100g):")
    for i, n in enumerate(alla_nv):
        print(f"  {i+1:2}. {n['namn']:<35} {n.get('varde', '–'):>8} {n.get('enhet','')}")

    print("\nAnge radnummer att ändra (kommaseparerat), eller Enter för att avbryta:")
    val = input("> ").strip()
    if val == "":
        return

    try:
        rader = [int(x.strip()) for x in val.split(",")]
    except ValueError:
        print("Ogiltigt val.")
        return

    andringar = list(alla_nv)  # kopia
    for rad in rader:
        if 1 <= rad <= len(alla_nv):
            n = andringar[rad - 1]
            nytt = input(f"  Nytt värde för '{n['namn']}' [{n.get('varde','')} {n.get('enhet','')}]: ").strip()
            try:
                andringar[rad - 1] = dict(n)
                andringar[rad - 1]['varde'] = float(nytt)
                print(f"  → {n['namn']} uppdaterad till {float(nytt)} {n.get('enhet','')}")
            except ValueError:
                print(f"  Ogiltigt värde, hoppas över.")

    # Spara till custom
    custom = ladda_custom()
    custom[str(nummer)] = dict(livsmedel)
    custom[str(nummer)]['naringsvarden_custom'] = andringar
    spara_custom(custom)
    print(f"\n'{namn}' sparad med egna näringsvärden.")


# ============================================================
# LÄGG TILL EGEN FÄRDIGRÄTT
# ============================================================

def lagg_till_fardigrat():
    """
    Skapar en helt ny färdigrätt och sparar den lokalt.
    Näringsvärden anges manuellt per 100g.
    """
    print("\n=== Lägg till egen färdigrätt ===")
    namn = input("Namn på rätten: ").strip()
    if not namn:
        print("Inget namn angivet.")
        return None

    metod = input("Tillagningsmetod (valfritt): ").strip()

    # Generera ett unikt negativt nummer för egna rätter
    custom = ladda_custom()
    egna_nummer = [int(k) for k in custom.keys() if int(k) < 0]
    nytt_nummer = min(egna_nummer) - 1 if egna_nummer else -1

    ny_ratt = {
        'nummer': nytt_nummer,
        'namn': namn,
        'livsmedelsTyp': 'Beräknat',
        'livsmedelsTypId': 99,
        'tillagningsmetod': metod,
        'naringsvarden_custom': []
    }

    print("\nAnge näringsvärden per 100g.")
    print("Lämna tomt för att hoppa över ett värde.\n")

    from naringsvarden import ALLA_NARINGSVARDEN
    naringsvarden = []
    for namn_nv in ALLA_NARINGSVARDEN:
        varde_str = input(f"  {namn_nv}: ").strip()
        if varde_str:
            try:
                naringsvarden.append({
                    'namn': namn_nv,
                    'varde': float(varde_str),
                    'enhet': ''
                })
            except ValueError:
                pass

    ny_ratt['naringsvarden_custom'] = naringsvarden

    custom[str(nytt_nummer)] = ny_ratt
    spara_custom(custom)
    print(f"\n'{namn}' sparad som egen färdigrätt (nr {nytt_nummer}).")
    return ny_ratt


# ============================================================
# LÄGG TILL I RECEPT – returnerar ingrediensobjekt
# ============================================================

def fardigrat_till_ingrediens(livsmedel, gram):
    """
    Konverterar en vald färdigrätt till ett ingrediensobjekt
    kompatibelt med recept.py.
    """
    return {
        'nummer': livsmedel['nummer'],
        'namn': livsmedel['namn'],
        'gram': gram,
        'typ': 'fardigrat'
    }


# ============================================================
# SÖKMENY – interaktivt flöde
# ============================================================

def sok_fardigrat_meny():
    """Interaktivt sökflöde för färdigrätter."""
    sokterm = input("Sök färdigrätt: ").strip()
    if not sokterm:
        return None

    resultat = sok_fardigratter(sokterm)
    print(f"\n{len(resultat)} träffar:")
    visa_sokresultat_fardigratter(resultat)

    vald = valj_fardigrat(resultat)
    if not vald:
        return None

    print("\nVad vill du göra?")
    print("  1. Visa näringsvärden")
    print("  2. Lägg till i recept")
    print("  3. Editera näringsvärden")
    val = input("Välj: ").strip()

    if val == "1":
        gram_str = input("Grammatur (Enter = 100g): ").strip()
        gram = float(gram_str) if gram_str else 100
        visa_fardigrat(vald, gram)
        return None

    elif val == "2":
        gram_str = input("Hur många gram? ").strip()
        try:
            gram = float(gram_str)
            ing = fardigrat_till_ingrediens(vald, gram)
            print(f"  '{vald['namn']}' ({gram:.0f}g) klar att lägga till i recept.")
            return ing
        except ValueError:
            print("Ogiltigt värde.")
            return None

    elif val == "3":
        editera_fardigrat(vald)
        return None

    return None