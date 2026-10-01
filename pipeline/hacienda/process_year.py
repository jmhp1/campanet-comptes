import sys, os, csv
from access_parser import AccessParser

YEAR = sys.argv[1]
DOWNLOAD_DIR = sys.argv[2]  # where the big .accdb files live (temporary, not committed)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))  # persistent, small CSV outputs
OUT_ENTITIES = os.path.join(OUT_DIR, "balears_entities.csv")
OUT_LIQ = os.path.join(OUT_DIR, "balears_liquidacio.csv")
OUT_PRES = os.path.join(OUT_DIR, "balears_pressupost_inicial.csv")
OUT_ROM = os.path.join(OUT_DIR, "balears_romanent.csv")

RMTE_CODES = {
    "fons_liquids": "011", "pendent_cobrar": "012", "pendent_pagar": "013",
    "partides_pendents_aplicacio": "2", "total": "01",
    "saldos_dubtos_cobrament": "02", "exces_financament_afectat": "03", "despeses_generals": "0",
}
RMTE_FIELDS = ["fons_liquids", "pendent_cobrar", "pendent_pagar", "partides_pendents_aplicacio",
               "total", "saldos_dubtos_cobrament", "exces_financament_afectat", "despeses_generals"]

def find_file(prefix):
    for ext in ("accdb", "mdb"):
        p = os.path.join(DOWNLOAD_DIR, f"{prefix}{YEAR}.{ext}")
        if os.path.exists(p):
            return p
    return os.path.join(DOWNLOAD_DIR, f"{prefix}{YEAR}.accdb")

def process_liquidaciones():
    path = find_file("Liquidaciones")
    db = AccessParser(path)
    inv = db.parse_table("tb_inventario")
    balears_idente = {}
    n = len(inv["idente"])
    for i in range(n):
        codente = inv["codente"][i].strip()
        if codente.startswith("07"):
            balears_idente[inv["idente"][i].strip()] = {
                "codente": codente,
                "nombreente": inv["nombreente"][i].strip(),
                "poblacio": inv["poblacion"][i].strip(),
                "estado": inv["estado"][i].strip(),
            }
    write_header = not os.path.exists(OUT_ENTITIES)
    with open(OUT_ENTITIES, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["any", "font", "idente", "codente", "nom", "poblacio", "estado"])
        for idente, d in balears_idente.items():
            w.writerow([YEAR, "liquidacions", idente, d["codente"], d["nombreente"], d["poblacio"], d["estado"]])

    eco = db.parse_table("tb_economica")
    ids = eco["idente"]
    cdcta = eco["cdcta"]
    rows_by_idente = {}
    for i in range(len(ids)):
        idv = ids[i].strip()
        if idv in balears_idente and len(cdcta[i].strip()) == 1:
            rows_by_idente.setdefault(idv, []).append(i)

    write_header = not os.path.exists(OUT_LIQ)
    with open(OUT_LIQ, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["any", "codente", "nom", "costat", "capitol", "definitiu", "executat"])
        for idv, idxs in rows_by_idente.items():
            d = balears_idente[idv]
            for i in idxs:
                costat = "despesa" if eco["tipreig"][i] == "G" else "ingres"
                w.writerow([YEAR, d["codente"], d["nombreente"], costat, cdcta[i].strip(), eco["imported"][i], eco["importer"][i]])

    if "tb_remanente" in db.catalog:
        rmt = db.parse_table("tb_remanente")
        ids_r = rmt["idente"]
        cdrmte = rmt["cdrmte"]
        by_idente = {}
        for i in range(len(ids_r)):
            idv = ids_r[i].strip()
            if idv in balears_idente:
                by_idente.setdefault(idv, {})[cdrmte[i].strip()] = rmt["importe"][i]
        write_header = not os.path.exists(OUT_ROM)
        with open(OUT_ROM, "a", newline="") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["any", "codente", "nom"] + RMTE_FIELDS)
            for idv, codes in by_idente.items():
                d = balears_idente[idv]
                row = [YEAR, d["codente"], d["nombreente"]]
                for field in RMTE_FIELDS:
                    row.append(codes.get(RMTE_CODES[field], ""))
                w.writerow(row)

    return len(balears_idente)

def process_presupuestos():
    path = find_file("Presupuestos")
    if not os.path.exists(path):
        return
    db = AccessParser(path)
    inv = db.parse_table("tb_inventario")
    balears_idente = {}
    n = len(inv["idente"])
    for i in range(n):
        codente = inv["codente"][i].strip()
        if codente.startswith("07"):
            balears_idente[inv["idente"][i].strip()] = {
                "codente": codente,
                "nombreente": inv["nombreente"][i].strip(),
            }
    eco = db.parse_table("tb_economica")
    ids = eco["idente"]
    cdcta = eco["cdcta"]
    write_header = not os.path.exists(OUT_PRES)
    with open(OUT_PRES, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["any", "codente", "nom", "costat", "capitol", "inicial"])
        for i in range(len(ids)):
            idv = ids[i].strip()
            if idv in balears_idente and len(cdcta[i].strip()) == 1:
                d = balears_idente[idv]
                costat = "despesa" if eco["tipreig"][i] == "G" else "ingres"
                w.writerow([YEAR, d["codente"], d["nombreente"], costat, cdcta[i].strip(), eco["importe"][i]])

n_entities = process_liquidaciones()
process_presupuestos()
print(f"{YEAR}: {n_entities} entitats de Balears trobades")
