# sok.py - Söklogik för livsmedel

from api import hamta_alla_livsmedel, hamta_kalorier

def sok_livsmedel(sokterm):
    """Söker efter livsmedel och returnerar en lista med träffar."""
    alla = hamta_alla_livsmedel()
    sokterm = sokterm.lower()
    return [l for l in alla if sokterm in l['namn'].lower()]

def visa_sokresultat(resultat):
    """Skriver ut sökresultaten med index."""
    if not resultat:
        print("Inga träffar.")
        return
    for i, l in enumerate(resultat):
        print(f"{i+1}. {l['namn']}")

def valj_livsmedel(resultat):
    """Låter användaren välja ett livsmedel från listan."""
    if not resultat:
        return None
    val = input("\nVälj nummer (eller Enter för att avbryta): ")
    if val == "":
        return None
    try:
        return resultat[int(val) - 1]
    except (ValueError, IndexError):
        print("Ogiltigt val.")
        return None

def sok_och_berakna():
    """Söker efter ett livsmedel och beräknar kalorier för angiven mängd."""
    sokterm = input("Sök livsmedel: ")
    resultat = sok_livsmedel(sokterm)
    visa_sokresultat(resultat)
    
    valt = valj_livsmedel(resultat)
    if not valt:
        return
    
    gram = input("Hur många gram? ")
    try:
        gram = float(gram)
    except ValueError:
        print("Ange ett giltigt antal gram.")
        return
    
    kcal_per_100g = hamta_kalorier(valt['nummer'])
    if kcal_per_100g is None:
        print("Kunde inte hämta kaloridata.")
        return
    
    totalt = kcal_per_100g * gram / 100
    print(f"\n{valt['namn']}: {totalt:.0f} kcal ({gram:.0f}g)")
    return {'livsmedel': valt, 'gram': gram, 'kcal': totalt}