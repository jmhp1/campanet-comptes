import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))

CAP_NOM = {
    "c1": "Personal", "c2": "Béns i serveis", "c3": "Interessos i comissions",
    "c4": "Transferències a tercers", "c5": "Fons de contingència", "c6": "Inversió",
    "c7": "Transferències de capital", "c8": "Actius financers", "c9": "Passius financers",
    "i1": "Impostos directes", "i2": "Impostos indirectes", "i3": "Taxes i preus",
    "i4": "Transferències corrents", "i5": "Ingressos patrimonials",
    "i6": "Alienació d'inversions reals", "i7": "Subvencions de capital",
    "i8": "Actius financers", "i9": "Passius financers",
}

def esc(v):
    return "'" + str(v).replace("'", "''") + "'"

with open(os.path.join(BASE, "esporles_liquidacio.csv")) as f:
    liq = list(csv.DictReader(f))
with open(os.path.join(BASE, "esporles_pressupost_inicial.csv")) as f:
    pres = {(r["any"], r["costat"], r["capitol"]): r["inicial"] for r in csv.DictReader(f)}
with open(os.path.join(BASE, "esporles_romanent.csv")) as f:
    rom = list(csv.DictReader(f))

ROM_FIELDS = ["fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
              "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]

with open(os.path.join(BASE, "d1_esporles.sql"), "w") as f:
    for r in liq:
        key = (r["any"], r["costat"], r["capitol"])
        inicial = pres.get(key, "")
        cap_nom = CAP_NOM.get(r["capitol"], r["capitol"])
        f.write(
            "INSERT INTO liquidacio_capitols (municipi, codi_ine, any, costat, capitol, nom, inicial, definitiu, executat) VALUES ("
            f"{esc(r['nom'])}, {esc(r['codente'])}, {r['any']}, {esc(r['costat'])}, {esc(r['capitol'])}, {esc(cap_nom)}, "
            f"{inicial or 'NULL'}, {r['definitiu']}, {r['executat']});\n"
        )
    for key, inicial in pres.items():
        any_, costat, cap = key
        if not any(r["any"] == any_ and r["costat"] == costat and r["capitol"] == cap for r in liq):
            cap_nom = CAP_NOM.get(cap, cap)
            f.write(
                "INSERT INTO liquidacio_capitols (municipi, codi_ine, any, costat, capitol, nom, inicial, definitiu, executat) VALUES ("
                f"{esc('Esporles')}, {esc('07020AA000')}, {any_}, {esc(costat)}, {esc(cap)}, {esc(cap_nom)}, {inicial}, NULL, NULL);\n"
            )
    for r in liq:
        key = (r["any"], r["costat"], r["capitol"])
        if key in pres:
            f.write(
                "INSERT INTO pressupost_inicial_capitols (municipi, codi_ine, any, costat, capitol, import_eur) VALUES ("
                f"{esc(r['nom'])}, {esc(r['codente'])}, {r['any']}, {esc(r['costat'])}, {esc(r['capitol'])}, {pres[key]});\n"
            )
    for r in rom:
        cols = ", ".join(ROM_FIELDS)
        vals = ", ".join(r[k] for k in ROM_FIELDS)
        f.write(
            f"INSERT INTO romanent_tresoreria (municipi, codi_ine, any, {cols}) VALUES "
            f"({esc(r['nom'])}, {esc(r['codente'])}, {r['any']}, {vals});\n"
        )

print("fet -> d1_esporles.sql")
