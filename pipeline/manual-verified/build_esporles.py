import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_pdf import parse_capitols, parse_romanent

BASE = os.path.dirname(os.path.abspath(__file__))
CODI = "07020AA000"
NOM = "Esporles"
YEARS = ["2017", "2018", "2020"]
TXT_DIR = "/tmp"  # esporles_{any}.txt generats amb pdftotext -layout

CAP_NOM = {
    "c1": "Personal", "c2": "Béns i serveis", "c3": "Interessos i comissions",
    "c4": "Transferències a tercers", "c5": "Fons de contingència", "c6": "Inversió",
    "c7": "Transferències de capital", "c8": "Actius financers", "c9": "Passius financers",
    "i1": "Impostos directes", "i2": "Impostos indirectes", "i3": "Taxes i preus",
    "i4": "Transferències corrents", "i5": "Ingressos patrimonials",
    "i6": "Alienació d'inversions reals", "i7": "Subvencions de capital",
    "i8": "Actius financers", "i9": "Passius financers",
}

liq_rows = []
pres_rows = []
rom_rows = []

for y in YEARS:
    path = os.path.join(TXT_DIR, f"esporles_{y}.txt")
    desp, ing = parse_capitols(path)
    for c, (i, d, e) in desp.items():
        liq_rows.append([y, CODI, NOM, "despesa", "c" + c, round(d, 2), round(e, 2)])
        pres_rows.append([y, CODI, NOM, "despesa", "c" + c, round(i, 2)])
    for c, (i, d, e) in ing.items():
        liq_rows.append([y, CODI, NOM, "ingres", "i" + c, round(d, 2), round(e, 2)])
        pres_rows.append([y, CODI, NOM, "ingres", "i" + c, round(i, 2)])
    rom = parse_romanent(path, y)
    if rom:
        rom_rows.append([y, CODI, NOM] + [round(rom[k], 2) for k in [
            "fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
            "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]])

with open(os.path.join(BASE, "esporles_liquidacio.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["any", "codente", "nom", "costat", "capitol", "definitiu", "executat"])
    w.writerows(liq_rows)

with open(os.path.join(BASE, "esporles_pressupost_inicial.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["any", "codente", "nom", "costat", "capitol", "inicial"])
    w.writerows(pres_rows)

with open(os.path.join(BASE, "esporles_romanent.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["any", "codente", "nom", "fons_liquids", "pendent_cobrar", "pendent_pagar",
                "partides_pendents_aplicacio", "total", "saldos_dubtos_cobrament",
                "exces_financament_afectat", "despeses_generals"])
    w.writerows(rom_rows)

print(f"liquidacio: {len(liq_rows)} files, pressupost: {len(pres_rows)} files, romanent: {len(rom_rows)} files")
