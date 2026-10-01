import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))

def nif_control_letter(cif_number_str):
    total = 0
    for i, ch in enumerate(cif_number_str):
        d = int(ch)
        pos = i + 1
        if pos % 2 == 1:
            total += sum(divmod(d * 2, 10))
        else:
            total += d
    units = total % 10
    control_digit = (10 - units) % 10
    letters = "JABCDEFGHI"
    return letters[control_digit]

EXCLUDE_CODI = {
    "07002AA000", "07015AA000", "07023AA000", "07024AA000", "07026AA000", "07032AA000",
    "07037AA000", "07046AA000", "07048AA000", "07050AA000", "07052AA000", "07054AA000",
    "07064AA000", "07902AA000",
}
# Municipis amb codi d'Hisenda irregular (segregats, no segueixen la numeració INE estàndard):
# el NIF real s'ha hagut de cercar manualment.
OVERRIDE_NIF = {
    "07901AA000": "P0706600D",  # Ariany, codi INE real 07066
}

def municipis_amb_nif():
    municipis = {}
    with open(os.path.join(BASE, "balears_entities.csv")) as f:
        for row in csv.DictReader(f):
            c = row["codente"]
            if not (c.endswith("AA000") and len(c) == 10):
                continue
            if c in EXCLUDE_CODI:
                continue
            nom = row["nom"].strip()
            any_ = row["any"]
            prev = municipis.get(c)
            if prev is None or any_ > prev[1]:
                municipis[c] = (nom, any_)

    out = {}
    for codi, (nom, _) in municipis.items():
        if codi in OVERRIDE_NIF:
            nif = OVERRIDE_NIF[codi]
        else:
            base = codi[:5] + "00"
            nif = "P" + base + nif_control_letter(base)
        out[codi] = {"nom": nom, "nif": nif}
    return out

if __name__ == "__main__":
    m = municipis_amb_nif()
    with open(os.path.join(BASE, "municipis_nif.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["codi_ine", "nom", "nif"])
        for codi, d in sorted(m.items(), key=lambda kv: kv[1]["nom"]):
            w.writerow([codi, d["nom"], d["nif"]])
    print(f"{len(m)} municipis amb NIF generat -> municipis_nif.csv")
