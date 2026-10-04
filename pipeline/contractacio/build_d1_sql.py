import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
CAMPANET_CODI = "07012AA000"

def esc(v):
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def numlit(v):
    if v is None or v == "":
        return "NULL"
    return v

with open(os.path.join(BASE, "contractes_mallorca.csv")) as f:
    rows = list(csv.DictReader(f))

n = 0
with open(os.path.join(BASE, "d1_contractes.sql"), "w") as f:
    f.write("ALTER TABLE contractes_plataforma ADD COLUMN codi_ine TEXT;\n")
    for r in rows:
        if r["codi_ine"] == CAMPANET_CODI and int(r["any"]) < 2022:
            continue  # ja tenim 2018-2021 de Campanet verificats a mà
        f.write(
            "INSERT INTO contractes_plataforma "
            "(municipi, codi_ine, any, expedient, objecte, procediment, estat, adjudicatari, "
            "nif_adjudicatari, import_adjudicat_amb_iva, pressupost_licitacio_amb_iva, enllac, verificat) VALUES ("
            f"{esc(r['municipi'])}, {esc(r['codi_ine'])}, {r['any']}, {esc(r['expedient'])}, "
            f"{esc(r['objecte'])}, {esc(r['procediment'])}, {esc(r['estat'])}, {esc(r['adjudicatari'])}, "
            f"{esc(r['nif_adjudicatari'])}, {numlit(r['import_adjudicat'])}, {numlit(r['pressupost_licitacio'])}, "
            f"{esc(r['enllac'])}, 'no');\n"
        )
        n += 1

print(f"{n} files SQL generades -> d1_contractes.sql")
