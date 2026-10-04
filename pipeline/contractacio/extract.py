import csv, os, re, zipfile
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw")
OUT_CSV = os.path.join(BASE, "contractes_mallorca.csv")

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "cac-place-ext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2",
    "cbc-place-ext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
}

PROCEDURE_NOM = {
    "1": "Obert", "2": "Restringit", "3": "Negociat sense publicitat",
    "4": "Negociat amb publicitat", "5": "Diàleg competitiu", "6": "Contracte menor",
    "7": "Derivat d'acord marc", "8": "Concurs de projectes", "9": "Obert simplificat",
    "10": "Associació per a la innovació", "11": "Derivat d'associació per a la innovació",
    "12": "Basat en sistema dinàmic d'adquisició", "13": "Licitació amb negociació",
    "100": "Normes internes", "999": "Altres",
}
STATUS_NOM = {
    "PRE": "Anunci previ", "PUB": "En termini", "EV": "Pendent d'adjudicació",
    "ADJ": "Adjudicada", "RES": "Resolta", "ANUL": "Anul·lada",
}

def load_municipis():
    by_nif = {}
    with open(os.path.join(BASE, "..", "hacienda", "municipis_nif.csv")) as f:
        for row in csv.DictReader(f):
            by_nif[row["nif"]] = {"codi_ine": row["codi_ine"], "nom": row["nom"]}
    return by_nif

def text(el, path):
    n = el.find(path, NS)
    return n.text.strip() if n is not None and n.text else None

def attr_text(el, path, attr):
    n = el.find(path, NS)
    return n.get(attr) if n is not None else None

def extract_entry(entry, municipis_by_nif):
    cfs = entry.find(".//cac-place-ext:ContractFolderStatus", NS)
    if cfs is None:
        return None
    lcp = cfs.find(".//cac-place-ext:LocatedContractingParty", NS)
    if lcp is None:
        return None
    nif_entitat = None
    for pid in lcp.findall(".//cac:PartyIdentification/cbc:ID", NS):
        if pid.get("schemeName") == "NIF":
            nif_entitat = pid.text.strip() if pid.text else None
    if nif_entitat not in municipis_by_nif:
        return None
    m = municipis_by_nif[nif_entitat]

    expedient = text(cfs, "cbc:ContractFolderID")
    estat_code = attr_text(cfs, "cbc-place-ext:ContractFolderStatusCode", None)
    estat_el = cfs.find("cbc-place-ext:ContractFolderStatusCode", NS)
    estat_code = estat_el.text.strip() if estat_el is not None and estat_el.text else None
    estat = STATUS_NOM.get(estat_code, estat_code)

    pp = cfs.find("cac:ProcurementProject", NS)
    objecte = text(pp, "cbc:Name") if pp is not None else None
    tp = cfs.find("cac:TenderingProcess", NS)
    proc_el = tp.find("cbc:ProcedureCode", NS) if tp is not None else None
    proc_code = proc_el.text.strip() if proc_el is not None and proc_el.text else None
    procediment = PROCEDURE_NOM.get(proc_code, proc_code)
    pressupost = None
    if pp is not None:
        ba = pp.find("cac:BudgetAmount", NS)
        if ba is not None:
            te = ba.find("cbc:TotalAmount", NS)
            pressupost = te.text.strip() if te is not None and te.text else None

    tr = cfs.find("cac:TenderResult", NS)
    adjudicatari = nif_adjudicatari = import_adj = None
    if tr is not None:
        wp = tr.find("cac:WinningParty", NS)
        if wp is not None:
            adjudicatari = text(wp, "cac:PartyName/cbc:Name")
            for pid in wp.findall("cac:PartyIdentification/cbc:ID", NS):
                if pid.get("schemeName") == "NIF":
                    nif_adjudicatari = pid.text.strip() if pid.text else None
        atp = tr.find("cac:AwardedTenderedProject/cac:LegalMonetaryTotal", NS)
        if atp is not None:
            pa = atp.find("cbc:PayableAmount", NS)
            import_adj = pa.text.strip() if pa is not None and pa.text else None
            if import_adj is None:
                te = atp.find("cbc:TaxExclusiveAmount", NS)
                import_adj = te.text.strip() if te is not None and te.text else None

    entry_id = text(entry, "a:id")
    link_el = entry.find("a:link", NS)
    link = link_el.get("href") if link_el is not None else None
    updated = text(entry, "a:updated")
    any_ = None
    if expedient:
        m2 = re.search(r"(20\d\d)", expedient)
        if m2:
            any_ = m2.group(1)
    if not any_ and updated:
        any_ = updated[:4]

    return {
        "entry_id": entry_id, "updated": updated,
        "codi_ine": m["codi_ine"], "municipi": m["nom"],
        "any": any_, "expedient": expedient, "objecte": objecte,
        "procediment": procediment, "estat": estat,
        "adjudicatari": adjudicatari, "nif_adjudicatari": nif_adjudicatari,
        "import_adjudicat": import_adj, "pressupost_licitacio": pressupost,
        "enllac": link,
    }

def process_year(year, municipis_by_nif, best_by_id):
    zpath = os.path.join(RAW, f"licitacions_{year}.zip")
    if not os.path.exists(zpath):
        print(f"{year}: no trobat")
        return 0
    n_found = 0
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if n.endswith(".atom")]
        for i, name in enumerate(names):
            try:
                data = z.read(name)
                root = ET.fromstring(data)
            except ET.ParseError:
                continue
            for entry in root.findall("a:entry", NS):
                rec = extract_entry(entry, municipis_by_nif)
                if rec is None:
                    continue
                n_found += 1
                key = rec["entry_id"]
                prev = best_by_id.get(key)
                if prev is None or (rec["updated"] or "") > (prev["updated"] or ""):
                    best_by_id[key] = rec
    print(f"{year}: {len(names)} fitxers, {n_found} coincidències (brutes, abans de desduplicar)")
    return n_found

def main():
    municipis_by_nif = load_municipis()
    best_by_id = {}
    for year in [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]:
        process_year(year, municipis_by_nif, best_by_id)

    fields = ["codi_ine", "municipi", "any", "expedient", "objecte", "procediment", "estat",
              "adjudicatari", "nif_adjudicatari", "import_adjudicat", "pressupost_licitacio",
              "enllac", "entry_id", "updated"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rec in sorted(best_by_id.values(), key=lambda r: (r["municipi"], r["any"] or "", r["expedient"] or "")):
            w.writerow(rec)
    print(f"\nTOTAL registres únics: {len(best_by_id)} -> {OUT_CSV}")

if __name__ == "__main__":
    main()
