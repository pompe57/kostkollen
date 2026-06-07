# naringsvarden.py - Hantering och visning av näringsvärden

import json
import os
from api import hamta_naringsvarden

# ============================================================
# KONFIGURATION – standardlista med 20 näringsämnen
# Användaren kan fritt ändra denna lista via installningar.json
# ============================================================

INSTALLNINGAR_FIL = "data/installningar.json"

STANDARD_NARINGSVARDEN = [
    "Energi (kcal)",
    "Energi (kJ)",
    "Protein",
    "Fett, totalt",
    "Summa mättade fettsyror",
    "Kolhydrater, tillgängliga",
    "Sockerarter, totalt",
    "Fiber",
    "Salt, NaCl",
    "Vatten",
    "Kolesterol",
    "Summa fleromättade fettsyror",
    "Summa enkelomättade fettsyror",
    "Vitamin D",
    "Vitamin C",
    "Folat, totalt",
    "Järn, Fe",
    "Kalcium, Ca",
    "Kalium, K",
    "Magnesium, Mg",
]

# Fullständig lista över alla tillgängliga näringsämnen – exakta API-namn
ALLA_NARINGSVARDEN = [
    "Energi (kcal)",
    "Energi (kJ)",
    "Protein",
    "Fett, totalt",
    "Kolhydrater, tillgängliga",
    "Fiber",
    "Sockerarter, totalt",
    "Monosackarider",
    "Disackarider",
    "Sackaros",
    "Tillsatt socker",
    "Fritt socker",
    "Fullkorn totalt",
    "Summa mättade fettsyror",
    "Summa enkelomättade fettsyror",
    "Summa fleromättade fettsyror",
    "Kolesterol",
    "Fettsyra 4:0-10:0",
    "Laurinsyra C12:0",
    "Myristinsyra C14:0",
    "Palmitinsyra C16:0",
    "Palmitoljesyra C16:1",
    "Stearinsyra C18:0",
    "Oljesyra C18:1",
    "Linolsyra C18:2",
    "Linolensyra C18:3",
    "Arakidinsyra C20:0",
    "Arakidonsyra C20:4",
    "EPA (C20:5)",
    "DPA (C22:5)",
    "DHA (C22:6)",
    "Fosfor, P",
    "Jod, I",
    "Järn, Fe",
    "Kalcium, Ca",
    "Kalium, K",
    "Magnesium, Mg",
    "Natrium, Na",
    "Salt, NaCl",
    "Selen, Se",
    "Zink, Zn",
    "Vitamin A",
    "Retinol",
    "Betakaroten/β-Karoten",
    "Vitamin D",
    "Vitamin E",
    "Tiamin",
    "Riboflavin",
    "Niacin",
    "Niacinekvivalenter",
    "Vitamin B6",
    "Folat, totalt",
    "Vitamin B12",
    "Vitamin C",
    "Vatten",
    "Aska",
    "Alkohol",
    "Avfall (skal etc.)",
]


# ============================================================
# INSTÄLLNINGAR – läs/spara valda näringsvärden
# ============================================================

def ladda_installningar():
    """Läser inställningar från fil, eller returnerar standardvärden."""
    if not os.path.exists(INSTALLNINGAR_FIL):
        return {"valda_naringsvarden": STANDARD_NARINGSVARDEN}
    with open(INSTALLNINGAR_FIL, "r", encoding="utf-8") as f:
        return json.load(f)

def spara_installningar(installningar):
    """Sparar inställningar till fil."""
    os.makedirs("data", exist_ok=True)
    with open(INSTALLNINGAR_FIL, "w", encoding="utf-8") as f:
        json.dump(installningar, f, ensure_ascii=False, indent=4)

def hamta_valda_naringsvarden():
    """Returnerar användarens valda lista med näringsvärdesnamn."""
    return ladda_installningar().get("valda_naringsvarden", STANDARD_NARINGSVARDEN)


# ============================================================
# FILTRERING – plocka ut valda näringsvärden från API-svar
# ============================================================

def filtrera_naringsvarden(naringsvarden_lista, valda=None):
    """
    Filtrerar en lista med näringsvärden från API:et.
    Returnerar bara de valda näringsämnena, i rätt ordning.
    """
    if valda is None:
        valda = hamta_valda_naringsvarden()

    # Bygg uppslagstabell: namn -> objekt
    index = {n['namn']: n for n in naringsvarden_lista}

    resultat = []
    for namn in valda:
        if namn in index:
            resultat.append(index[namn])
    return resultat

def hamta_och_filtrera(nummer, valda=None):
    """
    Hämtar näringsvärden för ett livsmedel och returnerar
    bara de valda näringsämnena.
    """
    alla = hamta_naringsvarden(nummer)
    return filtrera_naringsvarden(alla, valda)


# ============================================================
# BERÄKNING – skala näringsvärden efter gram
# ============================================================

def skala_naringsvarden(naringsvarden_lista, gram):
    """
    Skalar näringsvärden från per 100g till angiven grammatur.
    Returnerar en ny lista med justerade värden.
    """
    skalade = []
    for n in naringsvarden_lista:
        skalat = dict(n)
        if n.get('varde') is not None:
            skalat['varde'] = n['varde'] * gram / 100
        skalade.append(skalat)
    return skalade

def summera_naringsvarden(naringsvarden_per_ingrediens):
    """
    Summerar näringsvärden från flera ingredienser till ett recept-totalt.
    Tar en lista av redan skalade näringsvärdeslistor.
    Returnerar en summerad lista.
    """
    summerat = {}
    for naringslista in naringsvarden_per_ingrediens:
        for n in naringslista:
            namn = n['namn']
            if namn not in summerat:
                summerat[namn] = dict(n)
                summerat[namn]['varde'] = 0
            if n.get('varde') is not None:
                summerat[namn]['varde'] += n['varde']

    # Returnera i samma ordning som valda näringsvärden
    valda = hamta_valda_naringsvarden()
    return [summerat[namn] for namn in valda if namn in summerat]


# ============================================================
# VISNING – formaterad utskrift
# ============================================================

def visa_naringsvarden(naringsvarden_lista, rubrik=None, gram=None):
    """
    Skriver ut näringsvärden snyggt formaterat.
    Om gram anges visas värden per den grammaturen,
    annars visas per 100g (API-standard).
    """
    if rubrik:
        print(f"\n{'='*40}")
        print(f"  {rubrik}")
        if gram:
            print(f"  (per {gram:.0f}g)")
        print(f"{'='*40}")

    for n in naringsvarden_lista:
        namn  = n.get('namn', '?')
        varde = n.get('varde')
        enhet = n.get('enhet', '')
        if varde is None:
            print(f"  {namn:<35} –")
        else:
            print(f"  {namn:<35} {varde:>8.1f} {enhet}")


# ============================================================
# INSTÄLLNINGSMENY – välj egna näringsvärden
# ============================================================

def installningsmeny():
    """Låter användaren välja vilka 20 näringsvärden som visas."""
    print("\n=== Välj näringsvärden att visa ===")
    print("Nuvarande val markerat med [X]\n")

    valda = hamta_valda_naringsvarden()

    for i, namn in enumerate(ALLA_NARINGSVARDEN):
        markering = "[X]" if namn in valda else "[ ]"
        print(f"  {i+1:2}. {markering} {namn}")

    print("\nAnge nummer att växla (kommaseparerat), eller Enter för att spara:")
    val = input("> ").strip()

    if val == "":
        print("Inga ändringar gjorda.")
        return

    try:
        nummer_lista = [int(x.strip()) for x in val.split(",")]
    except ValueError:
        print("Ogiltigt val.")
        return

    for nr in nummer_lista:
        if 1 <= nr <= len(ALLA_NARINGSVARDEN):
            namn = ALLA_NARINGSVARDEN[nr - 1]
            if namn in valda:
                valda.remove(namn)
                print(f"  Borttagen: {namn}")
            else:
                valda.append(namn)
                print(f"  Tillagd:   {namn}")

    installningar = ladda_installningar()
    installningar["valda_naringsvarden"] = valda
    spara_installningar(installningar)
    print(f"\nSparat! {len(valda)} näringsvärden valda.")