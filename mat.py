# mat.py - Huvudprogram KostKollen

from sok import sok_livsmedel, visa_sokresultat, valj_livsmedel
from naringsvarden import (
    filtrera_naringsvarden,
    skala_naringsvarden,
    visa_naringsvarden,
    installningsmeny,
)
from recept import (
    skapa_recept,
    visa_recept,
    lista_recept,
    ta_bort_recept,
    berakna_annan_portion,
    fraga_tillagad_mangd,
)
from fardigratter import (
    sok_fardigratter,
    visa_sokresultat_fardigratter,
    valj_fardigrat,
    visa_fardigrat,
    lagg_till_fardigrat,
    fardigrat_till_ingrediens,
    editera_fardigrat,
)
from api import hamta_naringsvarden


# ============================================================
# LIVSMEDEL – sök råvara och visa näringsvärden
# ============================================================

def meny_livsmedel():
    """Söker efter en råvara och visar näringsvärden."""
    sokterm = input("Sök råvara: ").strip()
    if not sokterm:
        return

    resultat = sok_livsmedel(sokterm)
    # Visa bara Analyserade råvaror
    rawvaror = [l for l in resultat if l.get('livsmedelsTyp') == 'Analyserat']
    if not rawvaror:
        print("Inga råvaror hittades – prova ett annat sökord.")
        return

    visa_sokresultat(rawvaror)
    vald = valj_livsmedel(rawvaror)
    if not vald:
        return

    gram_str = input("Grammatur (Enter = 100g): ").strip()
    gram = float(gram_str) if gram_str else 100

    alla_nv = hamta_naringsvarden(vald['nummer'])
    filtrerade = filtrera_naringsvarden(alla_nv)
    if gram != 100:
        skalade = skala_naringsvarden(filtrerade, gram)
        visa_naringsvarden(skalade, rubrik=vald['namn'], gram=gram)
    else:
        visa_naringsvarden(filtrerade, rubrik=f"{vald['namn']} (per 100g)")


# ============================================================
# FÄRDIGRÄTTER – sök, visa, editera, lägg till
# ============================================================

def meny_fardigratter():
    while True:
        print("\n--- Färdigrätter ---")
        print("  1. Sök färdigrätt")
        print("  2. Lägg till egen färdigrätt")
        print("  0. Tillbaka")
        val = input("\nVälj: ").strip()

        if val == "1":
            _sok_och_visa_fardigrat()
        elif val == "2":
            lagg_till_fardigrat()
        elif val == "0":
            break
        else:
            print("Ogiltigt val.")

def _sok_och_visa_fardigrat():
    """Söker och visar en färdigrätt, med möjlighet att editera."""
    sokterm = input("Sök färdigrätt: ").strip()
    if not sokterm:
        return

    resultat = sok_fardigratter(sokterm)
    print(f"\n{len(resultat)} träffar:")
    visa_sokresultat_fardigratter(resultat)

    vald = valj_fardigrat(resultat)
    if not vald:
        return

    print("\nVad vill du göra?")
    print("  1. Visa näringsvärden")
    print("  2. Editera näringsvärden")
    val = input("Välj: ").strip()

    if val == "1":
        gram_str = input("Grammatur (Enter = 100g): ").strip()
        gram = float(gram_str) if gram_str else 100
        visa_fardigrat(vald, gram)
    elif val == "2":
        editera_fardigrat(vald)


# ============================================================
# RECEPTBOK – skapa, visa, lista, ta bort, portionsberäkna
# ============================================================

def meny_receptbok():
    while True:
        print("\n--- Receptbok ---")
        print("  1. Skapa nytt recept")
        print("  2. Visa recept")
        print("  3. Lista alla recept")
        print("  4. Ta bort recept")
        print("  5. Beräkna annan portion")
        print("  0. Tillbaka")
        val = input("\nVälj: ").strip()

        if val == "1":
            _recept_inmatning()
        elif val == "2":
            namn = input("Receptets namn: ").strip()
            visa_recept(namn)
        elif val == "3":
            lista_recept()
        elif val == "4":
            lista_recept()
            namn = input("\nAnge namn på recept att ta bort: ").strip()
            bekrafta = input(f"Är du säker på att du vill ta bort '{namn}'? (j/n): ").strip()
            if bekrafta.lower() == 'j':
                ta_bort_recept(namn)
        elif val == "5":
            lista_recept()
            namn = input("\nAnge receptnamn: ").strip()
            berakna_annan_portion(namn)
        elif val == "0":
            break
        else:
            print("Ogiltigt val.")

def _recept_inmatning():
    """Hanterar inmatning av ett nytt recept med råvaror och/eller färdigrätter."""
    namn = input("Receptets namn: ").strip()
    if not namn:
        print("Inget namn angivet.")
        return

    ingredienser = []

    while True:
        print("\n--- Lägg till ingrediens ---")
        print("  1. Råvara")
        print("  2. Färdigrätt")
        print("  0. Klar – gå vidare")
        val = input("Välj: ").strip()

        if val == "0":
            break

        elif val == "1":
            sokterm = input("Sök råvara: ").strip()
            if not sokterm:
                continue
            resultat = sok_livsmedel(sokterm)
            rawvaror = [l for l in resultat if l.get('livsmedelsTyp') == 'Analyserat']
            if not rawvaror:
                print("Inga råvaror hittades.")
                continue
            visa_sokresultat(rawvaror)
            vald = valj_livsmedel(rawvaror)
            if not vald:
                continue
            gram_str = input("Hur många gram? ").strip()
            try:
                gram = float(gram_str)
                ingredienser.append({
                    'nummer': vald['nummer'],
                    'namn': vald['namn'],
                    'gram': gram,
                    'typ': 'ravaror'
                })
                print(f"  ✓ {vald['namn']} ({gram:.0f}g) tillagd.")
            except ValueError:
                print("Ogiltigt antal gram.")

        elif val == "2":
            sokterm = input("Sök färdigrätt: ").strip()
            if not sokterm:
                continue
            resultat = sok_fardigratter(sokterm)
            print(f"\n{len(resultat)} träffar:")
            visa_sokresultat_fardigratter(resultat)
            vald = valj_fardigrat(resultat)
            if not vald:
                continue
            gram_str = input("Hur många gram? ").strip()
            try:
                gram = float(gram_str)
                ing = fardigrat_till_ingrediens(vald, gram)
                ingredienser.append(ing)
                print(f"  ✓ {vald['namn']} ({gram:.0f}g) tillagd.")
            except ValueError:
                print("Ogiltigt antal gram.")

        else:
            print("Ogiltigt val.")

    if not ingredienser:
        print("Inga ingredienser – receptet sparades inte.")
        return

    # Visa sammanfattning
    print(f"\nIngredienser i '{namn}':")
    for ing in ingredienser:
        print(f"  {ing['namn']:<35} {ing['gram']:>6.0f}g")

    # Tillagad mängd och portioner
    tillagad_gram, tillagad_enhet = fraga_tillagad_mangd()
    if tillagad_gram <= 0:
        print("Ogiltig mängd – receptet sparades inte.")
        return

    portioner_str = input("Antal portioner: ").strip()
    try:
        portioner = int(portioner_str)
    except ValueError:
        print("Ogiltigt antal portioner.")
        return

    skapa_recept(namn, ingredienser, tillagad_gram, tillagad_enhet, portioner)


# ============================================================
# INSTÄLLNINGAR
# ============================================================

def meny_installningar():
    while True:
        print("\n--- Inställningar ---")
        print("  1. Välj näringsvärden att visa")
        print("  0. Tillbaka")
        val = input("\nVälj: ").strip()

        if val == "1":
            installningsmeny()
        elif val == "0":
            break
        else:
            print("Ogiltigt val.")


# ============================================================
# HUVUDMENY
# ============================================================

def huvudmeny():
    while True:
        print("\n" + "="*40)
        print("  KostKollen")
        print("="*40)
        print("  1. Sök livsmedel")
        print("  2. Färdigrätter")
        print("  3. Receptbok")
        print("  4. Inställningar")
        print("  0. Avsluta")

        val = input("\nVälj: ").strip()

        if val == "1":
            meny_livsmedel()
        elif val == "2":
            meny_fardigratter()
        elif val == "3":
            meny_receptbok()
        elif val == "4":
            meny_installningar()
        elif val == "0":
            print("\nHejdå!")
            break
        else:
            print("Ogiltigt val, försök igen.")

huvudmeny()