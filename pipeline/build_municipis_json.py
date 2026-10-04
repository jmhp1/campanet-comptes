"""Construeix data/municipis_mallorca.json a partir de:
  - pipeline/hacienda/balears_*.csv (Ministeri d'Hisenda, CONPREL)
  - pipeline/manual-verified/*_liquidacio.csv / *_pressupost_inicial.csv / *_romanent.csv
    (dades tretes de les webs dels ajuntaments, substitueixen/completen les del Ministeri)
  - pipeline/contractacio/contractes_mallorca.csv

Torna a córrer aquest script sempre que s'afegeixi un municipi nou a manual-verified/
o es torni a baixar un any del Ministeri. És l'única font de veritat del JSON del dashboard.
"""
import csv, glob, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
HACIENDA = os.path.join(BASE, "hacienda")
MANUAL = os.path.join(BASE, "manual-verified")
CONTR = os.path.join(BASE, "contractacio", "contractes_mallorca.csv")
OUT = os.path.join(os.path.dirname(BASE), "data", "municipis_mallorca.json")

# Exclosos per codi: no són municipis de Mallorca (Menorca/Eivissa/Formentera) o no són
# municipis (consells insulars, etc. acaben en DD000/altres sufixos, es filtren per patró).
EXCLUDE_CODI = {
    "07002AA000", "07015AA000", "07023AA000", "07024AA000", "07026AA000",
    "07032AA000", "07037AA000", "07046AA000", "07048AA000", "07050AA000",
    "07052AA000", "07054AA000", "07064AA000", "07902AA000",
}
CAMPANET_CODI = "07012AA000"

# Correccions de grafia: el nom oficial del Ministeri no sempre és el català correcte,
# i alguns venen amb l'article mogut al final per ordenar ("Pobla (Sa)").
NOM_FIX = {
    "Deyá": "Deià",
    "Santa María del Camí": "Santa Maria del Camí",
    "Pobla (Sa)": "Sa Pobla",
    "Salines (Ses)": "Ses Salines",
}

def fix_nom(nom):
    return NOM_FIX.get(nom, nom)

# Puigpunyent i Sineu no surten MAI a tb_inventario del fitxer "Liquidaciones" del Ministeri
# (cap any 2016-2024), només al de "Presupuestos" — per això falten de balears_entities.csv
# encara que sí que tenen pressupost inicial. Sense aquesta llista no apareixen al desplegable.
MANUAL_MUNICIPIS = {
    "07045AA000": {"nom": "Puigpunyent", "poblacio": 1100},
    "07060AA000": {"nom": "Sineu", "poblacio": 4000},
}

def is_municipi_mallorca(codi):
    return codi.endswith("AA000") and codi not in EXCLUDE_CODI and codi != CAMPANET_CODI

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def to_float(v):
    if v is None or v == "":
        return None
    return float(v)

# ---------- municipis (nom + població, l'any més recent disponible a l'inventari) ----------
municipis = {}
for row in read_csv(os.path.join(HACIENDA, "balears_entities.csv")):
    codi = row["codente"]
    if not is_municipi_mallorca(codi):
        continue
    municipis[codi] = {"codi": codi, "nom": fix_nom(row["nom"].strip()), "poblacio": int(float(row["poblacio"]))}
for codi, info in MANUAL_MUNICIPIS.items():
    municipis.setdefault(codi, {"codi": codi, "nom": info["nom"], "poblacio": info["poblacio"]})

# ---------- liquidacio[codi][any][cap] = {inicial, definitiu, executat} ----------
liquidacio = {}
def ensure_cell(codi, any_, cap):
    liquidacio.setdefault(codi, {}).setdefault(any_, {}).setdefault(cap, {"inicial": None, "definitiu": None, "executat": None})
    return liquidacio[codi][any_][cap]

def norm_cap(costat, capitol_raw):
    """El Ministeri dona el capítol com a dígit nu ('7'); manual-verified ja ve prefixat ('c7'/'i7')."""
    capitol_raw = capitol_raw.strip()
    if capitol_raw[0] in "ci":
        return capitol_raw
    return ("c" if costat == "despesa" else "i") + capitol_raw

def load_liquidacio(path, source_label):
    for row in read_csv(path):
        codi = row.get("codente") or row.get("codi_ine")
        if not is_municipi_mallorca(codi) and codi not in MANUAL_MUNICIPIS:
            continue
        cap = norm_cap(row["costat"], row["capitol"])
        cell = ensure_cell(codi, row["any"], cap)
        cell["definitiu"] = to_float(row.get("definitiu"))
        cell["executat"] = to_float(row.get("executat"))

def load_pressupost(path):
    for row in read_csv(path):
        codi = row.get("codente") or row.get("codi_ine")
        if not is_municipi_mallorca(codi) and codi not in MANUAL_MUNICIPIS:
            continue
        cap = norm_cap(row["costat"], row["capitol"])
        cell = ensure_cell(codi, row["any"], cap)
        cell["inicial"] = to_float(row.get("inicial"))

load_liquidacio(os.path.join(HACIENDA, "balears_liquidacio.csv"), "ministeri")
load_pressupost(os.path.join(HACIENDA, "balears_pressupost_inicial.csv"))

# Fitxers manual-verified/*_liquidacio.csv i *_pressupost_inicial.csv: mateix esquema,
# sobreescriuen (no sumen) la cel·la del Ministeri si n'hi havia, perquè són font primària.
for path in sorted(glob.glob(os.path.join(MANUAL, "*_liquidacio.csv"))):
    load_liquidacio(path, "web")
for path in sorted(glob.glob(os.path.join(MANUAL, "*_pressupost_inicial.csv"))):
    load_pressupost(path)

# ---------- romanent[codi][any] = {...8 camps...} ----------
ROM_FIELDS = ["fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
              "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]

romanent = {}
def load_romanent(path):
    for row in read_csv(path):
        codi = row["codente"] if "codente" in row else row.get("codi_ine")
        if not is_municipi_mallorca(codi) and codi not in MANUAL_MUNICIPIS:
            continue
        romanent.setdefault(codi, {})[row["any"]] = {k: to_float(row.get(k)) for k in ROM_FIELDS}

load_romanent(os.path.join(HACIENDA, "balears_romanent.csv"))
for path in sorted(glob.glob(os.path.join(MANUAL, "*_romanent.csv"))):
    load_romanent(path)

# ---------- contractes[codi] = [...] ----------
contractes = {}
for row in read_csv(CONTR):
    codi = row["codi_ine"]
    if not is_municipi_mallorca(codi) and codi not in MANUAL_MUNICIPIS:
        continue
    contractes.setdefault(codi, []).append({
        "any": row["any"], "exp": row["expedient"], "obj": row["objecte"], "proc": row["procediment"],
        "estat": row["estat"], "adj": row["adjudicatari"] or None,
        "imp": to_float(row["import_adjudicat"]), "pres": to_float(row["pressupost_licitacio"]),
        "link": row["enllac"],
    })

municipis_list = sorted(municipis.values(), key=lambda m: m["poblacio"])

out = {
    "municipis": municipis_list,
    "liquidacio": liquidacio,
    "romanent": romanent,
    "contractes": contractes,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print(f"{len(municipis_list)} municipis, {sum(len(v) for v in liquidacio.values())} caselles any de liquidacio/pressupost, "
      f"{sum(len(v) for v in contractes.values())} contractes -> {OUT}")
