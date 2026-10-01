import csv
import os

DIR = os.path.dirname(os.path.abspath(__file__))
IN_PRES = os.path.join(DIR, "balears_pressupost_inicial.csv")
IN_LIQ = os.path.join(DIR, "balears_liquidacio.csv")
OUT_SQL = os.path.join(DIR, "mallorca_liquidacio.sql")

CAMPANET = "07012AA000"

# Entitats de Balears que NO són de Mallorca (Menorca, Eivissa, Formentera),
# identificades pel seu codi d'entitat (prefix "07" + codi INE de municipi + "AA000").
NO_MALLORCA = {
    # Menorca
    "07002AA000",  # Alaior
    "07015AA000",  # Ciutadella de Menorca
    "07023AA000",  # Ferreries
    "07032AA000",  # Maó
    "07037AA000",  # Mercadal (Es)
    "07052AA000",  # Sant Lluís
    "07064AA000",  # Castell (Es)
    "07902AA000",  # Migjorn Gran (Es)
    # Eivissa
    "07026AA000",  # Eivissa
    "07046AA000",  # Sant Antoni de Portmany
    "07048AA000",  # Sant Josep de sa Talaia
    "07050AA000",  # Sant Joan de Labritja
    "07054AA000",  # Santa Eulària des Riu
    # Formentera
    "07024AA000",  # Formentera
}


def is_mallorca_ajuntament(codente):
    return codente.endswith("AA000") and codente not in NO_MALLORCA and codente != CAMPANET


def capitol_key(costat, capitol_num):
    prefix = "c" if costat == "despesa" else "i"
    return f"{prefix}{capitol_num}"


def load(path, value_cols):
    """Retorna dict (codente, any, costat, capitol) -> dict de valors, i codente -> nom."""
    data = {}
    noms = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            codente = row["codente"]
            if not is_mallorca_ajuntament(codente):
                continue
            noms[codente] = row["nom"]
            key = (codente, row["any"], row["costat"], capitol_key(row["costat"], row["capitol"]))
            data[key] = {col: row[col] for col in value_cols}
    return data, noms


def sql_literal(value):
    if value is None:
        return "NULL"
    return value


def sql_string(value):
    return "'" + value.replace("'", "''") + "'"


def main():
    pres, noms_pres = load(IN_PRES, ["inicial"])
    liq, noms_liq = load(IN_LIQ, ["definitiu", "executat"])
    noms = {**noms_pres, **noms_liq}

    keys = sorted(set(pres) | set(liq), key=lambda k: (noms[k[0]], int(k[1]), k[2], k[3]))

    lines = []
    lines.append(
        "CREATE TABLE IF NOT EXISTS liquidacio_mallorca_hisenda (\n"
        "  codente TEXT NOT NULL,\n"
        "  nom TEXT NOT NULL,\n"
        "  any INTEGER NOT NULL,\n"
        "  costat TEXT NOT NULL CHECK (costat IN ('ingres', 'despesa')),\n"
        "  capitol TEXT NOT NULL,\n"
        "  inicial REAL,\n"
        "  definitiu REAL,\n"
        "  executat REAL,\n"
        "  PRIMARY KEY (codente, any, costat, capitol)\n"
        ");"
    )

    n_rows = 0
    for key in keys:
        codente, any_, costat, capitol = key
        nom = noms[codente]
        inicial = pres.get(key, {}).get("inicial")
        definitiu = liq.get(key, {}).get("definitiu")
        executat = liq.get(key, {}).get("executat")
        values = ", ".join(
            [
                sql_string(codente),
                sql_string(nom),
                any_,
                sql_string(costat),
                sql_string(capitol),
                sql_literal(inicial),
                sql_literal(definitiu),
                sql_literal(executat),
            ]
        )
        lines.append(
            "INSERT INTO liquidacio_mallorca_hisenda "
            "(codente, nom, any, costat, capitol, inicial, definitiu, executat) "
            f"VALUES ({values});"
        )
        n_rows += 1

    with open(OUT_SQL, "w") as f:
        f.write("\n".join(lines) + "\n")

    n_municipis = len(set(noms))
    print(f"{n_rows} files, {n_municipis} municipis de Mallorca (sense Campanet) -> {OUT_SQL}")


if __name__ == "__main__":
    main()
