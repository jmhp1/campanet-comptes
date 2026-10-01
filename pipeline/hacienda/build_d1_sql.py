import csv, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = BASE

# Exclosos per codi (no per nom: el mateix municipi pot aparèixer amb grafies diferents
# segons l'any, p. ex. "Santa Eulària des Riu" / "Santa Eulalia del Río").
EXCLUDE_CODI = {
    "07002AA000",  # Alaior (Menorca)
    "07015AA000",  # Ciutadella de Menorca
    "07023AA000",  # Ferreries (Menorca)
    "07024AA000",  # Formentera
    "07026AA000",  # Eivissa
    "07032AA000",  # Maó (Menorca)
    "07037AA000",  # Es Mercadal (Menorca)
    "07046AA000",  # Sant Antoni de Portmany (Eivissa)
    "07048AA000",  # Sant Josep de sa Talaia (Eivissa)
    "07050AA000",  # Sant Joan de Labritja (Eivissa)
    "07052AA000",  # Sant Lluís (Menorca)
    "07054AA000",  # Santa Eulària des Riu (Eivissa)
    "07064AA000",  # Es Castell (Menorca)
    "07902AA000",  # Es Migjorn Gran (Menorca)
}
CAMPANET_CODI = "07012AA000"

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
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def numlit(v):
    if v is None or v == "":
        return "NULL"
    return v

# --- 1. municipis (Mallorca, from balears_entities.csv, excluding Campanet) ---
municipis = {}  # codi_ine -> {nom, poblacio(latest any)}
with open(os.path.join(BASE, "balears_entities.csv")) as f:
    for row in csv.DictReader(f):
        c = row["codente"]
        if not (c.endswith("AA000") and len(c) == 10):
            continue
        nom = row["nom"].strip()
        if c in EXCLUDE_CODI or c == CAMPANET_CODI:
            continue
        prev = municipis.get(c)
        if prev is None or row["any"] > prev["any"]:
            municipis[c] = {"nom": nom, "poblacio": row["poblacio"].strip(), "any": row["any"]}

mallorca_codis = set(municipis.keys())

# --- 2. merge liquidacio (definitiu/executat) + pressupost inicial (inicial) ---
merged = {}  # (codi, any, costat, capitol) -> {definitiu, executat, inicial}
with open(os.path.join(BASE, "balears_liquidacio.csv")) as f:
    for row in csv.DictReader(f):
        c = row["codente"]
        if c not in mallorca_codis:
            continue
        key = (c, row["any"], row["costat"], row["capitol"])
        merged.setdefault(key, {})["definitiu"] = row["definitiu"]
        merged.setdefault(key, {})["executat"] = row["executat"]

with open(os.path.join(BASE, "balears_pressupost_inicial.csv")) as f:
    for row in csv.DictReader(f):
        c = row["codente"]
        if c not in mallorca_codis:
            continue
        key = (c, row["any"], row["costat"], row["capitol"])
        merged.setdefault(key, {})["inicial"] = row["inicial"]

# --- 2b. romanent de tresoreria ---
ROM_FIELDS = ["fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
              "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]
romanent = []  # list of (codi, any, {field: val})
with open(os.path.join(BASE, "balears_romanent.csv")) as f:
    for row in csv.DictReader(f):
        c = row["codente"]
        if c not in mallorca_codis:
            continue
        romanent.append((c, row["any"], {k: row[k] for k in ROM_FIELDS}))

# --- write SQL ---
with open(os.path.join(OUT_DIR, "d1_schema_update.sql"), "w") as f:
    f.write("ALTER TABLE liquidacio_capitols ADD COLUMN codi_ine TEXT;\n")
    f.write("ALTER TABLE pressupost_inicial_capitols ADD COLUMN codi_ine TEXT;\n")
    f.write(f"UPDATE liquidacio_capitols SET codi_ine = '{CAMPANET_CODI}' WHERE municipi = 'Campanet';\n")
    f.write(f"UPDATE pressupost_inicial_capitols SET codi_ine = '{CAMPANET_CODI}' WHERE municipi = 'Campanet';\n")
    f.write("ALTER TABLE romanent_tresoreria ADD COLUMN codi_ine TEXT;\n")
    f.write(f"UPDATE romanent_tresoreria SET codi_ine = '{CAMPANET_CODI}' WHERE municipi = 'Campanet';\n")
    f.write("""CREATE TABLE municipis (
  codi_ine TEXT PRIMARY KEY,
  nom TEXT NOT NULL,
  illa TEXT NOT NULL DEFAULT 'Mallorca',
  poblacio INTEGER
);\n""")

with open(os.path.join(OUT_DIR, "d1_municipis.sql"), "w") as f:
    f.write(f"INSERT INTO municipis (codi_ine, nom, illa, poblacio) VALUES ({esc(CAMPANET_CODI)}, 'Campanet', 'Mallorca', 2824);\n")
    for codi, d in sorted(municipis.items()):
        pob = d["poblacio"].rstrip(".") if d["poblacio"] else None
        f.write(f"INSERT INTO municipis (codi_ine, nom, illa, poblacio) VALUES ({esc(codi)}, {esc(d['nom'])}, 'Mallorca', {numlit(pob)});\n")

n_liq = 0
with open(os.path.join(OUT_DIR, "d1_liquidacio_mallorca.sql"), "w") as f:
    for (codi, any_, costat, capitol), vals in sorted(merged.items()):
        nom_municipi = municipis[codi]["nom"]
        cap_key = ("c" if costat == "despesa" else "i") + capitol
        cap_nom = CAP_NOM.get(cap_key, cap_key)
        inicial = numlit(vals.get("inicial"))
        definitiu = numlit(vals.get("definitiu"))
        executat = numlit(vals.get("executat"))
        f.write(
            f"INSERT INTO liquidacio_capitols (municipi, codi_ine, any, costat, capitol, nom, inicial, definitiu, executat) VALUES "
            f"({esc(nom_municipi)}, {esc(codi)}, {any_}, {esc(costat)}, {esc(cap_key)}, {esc(cap_nom)}, {inicial}, {definitiu}, {executat});\n"
        )
        n_liq += 1

n_pres = 0
with open(os.path.join(OUT_DIR, "d1_pressupost_inicial_mallorca.sql"), "w") as f:
    for (codi, any_, costat, capitol), vals in sorted(merged.items()):
        if "inicial" not in vals:
            continue
        nom_municipi = municipis[codi]["nom"]
        cap_key = ("c" if costat == "despesa" else "i") + capitol
        f.write(
            f"INSERT INTO pressupost_inicial_capitols (municipi, codi_ine, any, costat, capitol, import_eur) VALUES "
            f"({esc(nom_municipi)}, {esc(codi)}, {any_}, {esc(costat)}, {esc(cap_key)}, {numlit(vals['inicial'])});\n"
        )
        n_pres += 1

n_rom = 0
with open(os.path.join(OUT_DIR, "d1_romanent_mallorca.sql"), "w") as f:
    for codi, any_, vals in sorted(romanent, key=lambda r: (r[0], r[1])):
        nom_municipi = municipis[codi]["nom"]
        cols = ", ".join(ROM_FIELDS)
        vallist = ", ".join(numlit(vals[k]) for k in ROM_FIELDS)
        f.write(
            f"INSERT INTO romanent_tresoreria (municipi, codi_ine, any, {cols}) VALUES "
            f"({esc(nom_municipi)}, {esc(codi)}, {any_}, {vallist});\n"
        )
        n_rom += 1

print(f"municipis: {len(municipis)}")
print(f"liquidacio_capitols rows: {n_liq}")
print(f"pressupost_inicial_capitols rows: {n_pres}")
print(f"romanent_tresoreria rows: {n_rom}")
