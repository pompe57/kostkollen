# mat.py - Huvudprogram

from sok import sok_och_berakna

def meny():
    while True:
        print("\n=== KostKollen ===")
        print("1. Sök livsmedel")
        print("0. Avsluta")
        
        val = input("\nVälj: ")
        
        if val == "1":
            sok_och_berakna()
        elif val == "0":
            print("Hejdå!")
            break
        else:
            print("Ogiltigt val, försök igen.")

meny()