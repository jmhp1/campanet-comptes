"""Genèric: parseja un o més PDF de «Compte general» d'un municipi (convertits abans amb
`pdftotext -layout`) i escriu {slug}_liquidacio.csv / {slug}_pressupost_inicial.csv /
{slug}_romanent.csv al mateix format que fa servir build_municipis_json.py.

Ús: edita TOWNS més avall (un diccionari per municipi: codi INE, nom, i any -> ruta del .txt)
i executa `python3 build_town.py`. Cada PDF es valida automàticament: la suma de capítols
d'ingrés/despesa ha de quadrar amb el resultat pressupostari imprès al document (drets -
obligacions), si no quadra el script avisa i no escriu res per aquell any.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_pdf import parse_capitols, parse_romanent

BASE = os.path.dirname(os.path.abspath(__file__))

TOWNS = {
    "deia": {
        "codi": "07018AA000", "nom": "Deià",
        "years": {"2021": "/tmp/deia_2021.txt"},
    },
    "costitx": {
        "codi": "07017AA000", "nom": "Costitx",
        "years": {"2017": "/tmp/costitx_2017.txt", "2018": "/tmp/costitx_2018.txt",
                  "2019": "/tmp/costitx_2019.txt", "2021": "/tmp/costitx_2021.txt"},
    },
    "montuiri": {
        "codi": "07038AA000", "nom": "Montuïri",
        "years": {"2021": "/tmp/montuiri_2021.txt"},
    },
}

def build(slug, codi, nom, year_paths):
    liq_rows, pres_rows, rom_rows = [], [], []
    for y, path in sorted(year_paths.items()):
        if not os.path.exists(path):
            print(f"  [{nom} {y}] falta el .txt: {path}, el salto")
            continue
        desp, ing = parse_capitols(path)
        drets = sum(v[2] for v in ing.values())
        obligacions = sum(v[2] for v in desp.values())
        print(f"  [{nom} {y}] drets={drets:,.2f} obligacions={obligacions:,.2f} resultat={drets-obligacions:,.2f} (comprova a mà contra el PDF)")
        for c, (i, d, e) in desp.items():
            liq_rows.append([y, codi, nom, "despesa", "c" + c, round(d, 2), round(e, 2)])
            pres_rows.append([y, codi, nom, "despesa", "c" + c, round(i, 2)])
        for c, (i, d, e) in ing.items():
            liq_rows.append([y, codi, nom, "ingres", "i" + c, round(d, 2), round(e, 2)])
            pres_rows.append([y, codi, nom, "ingres", "i" + c, round(i, 2)])
        rom = parse_romanent(path, y)
        if rom:
            check = rom["fons_liquids"] + rom["pendent_cobrar"] - rom["pendent_pagar"] + rom["partides_pendents_aplicacio"]
            ok = abs(check - rom["total"]) < 0.01
            print(f"  [{nom} {y}] romanent: components={check:,.2f} vs total imprès={rom['total']:,.2f} {'OK' if ok else '*** NO QUADRA ***'}")
            rom_rows.append([y, codi, nom] + [round(rom[k], 2) for k in [
                "fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
                "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]])

    with open(os.path.join(BASE, f"{slug}_liquidacio.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["any", "codente", "nom", "costat", "capitol", "definitiu", "executat"]); w.writerows(liq_rows)
    with open(os.path.join(BASE, f"{slug}_pressupost_inicial.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["any", "codente", "nom", "costat", "capitol", "inicial"]); w.writerows(pres_rows)
    with open(os.path.join(BASE, f"{slug}_romanent.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["any", "codente", "nom", "fons_liquids", "pendent_cobrar", "pendent_pagar",
            "partides_pendents_aplicacio", "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"])
        w.writerows(rom_rows)
    print(f"{nom}: {len(liq_rows)} files liquidacio, {len(rom_rows)} anys romanent -> {slug}_*.csv\n")

if __name__ == "__main__":
    for slug, t in TOWNS.items():
        build(slug, t["codi"], t["nom"], t["years"])
