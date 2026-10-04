import re, sys

NUM = r"-?[\d.]+,\d{2}"

def parse_num(s):
    return float(s.replace(".", "").replace(",", "."))

def get_section_lines(lines, start_text, stop_texts):
    start_i = None
    for i, l in enumerate(lines):
        if start_text in l:
            start_i = i + 1
            break
    if start_i is None:
        return []
    stop_i = len(lines)
    for i in range(start_i, len(lines)):
        if any(st in lines[i] for st in stop_texts):
            stop_i = i
            break
    return lines[start_i:stop_i]

def extract_rows(section_lines, n_cols, pattern):
    rows = []
    for line in section_lines:
        m = re.match(pattern, line)
        if not m:
            continue
        econ = m.group(1)
        nums = re.findall(NUM, line)
        if len(nums) < n_cols:
            continue
        nums = [parse_num(n) for n in nums[-n_cols:]]
        rows.append((econ, nums))
    return rows

def aggregate(rows, inicial_idx, definitiu_idx, executat_idx):
    cap = {}
    for econ, nums in rows:
        c = econ[0]
        d = cap.setdefault(c, [0.0, 0.0, 0.0])
        d[0] += nums[inicial_idx]
        d[1] += nums[definitiu_idx]
        d[2] += nums[executat_idx]
    return cap

def parse_capitols(path):
    """Parsa l'Estat de Liquidació del Pressupost (resum per econòmica) d'un compte general
    en format ICAL normal, extret amb `pdftotext -layout`. Agrega per capítol (primer dígit
    del codi econòmic). Validat contra Esporles 2017/2018/2020: quadra al cèntim amb els
    totals impresos al document (inicial=inicial, definitiu=definitiu entre despesa i ingrés)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    desp_lines = get_section_lines(lines, "SITUACIÓ DE DESPESES", ["SITUACIÓ D'INGRESSOS"])
    ing_lines = get_section_lines(lines, "SITUACIÓ D'INGRESSOS", ["RESULTAT PRESSUPOSTARI", "ESTAT DE FLUXES"])
    desp_rows = extract_rows(desp_lines, 8, r"^\d{1,2}\s+\S+\s+(\d{3,5})\s+.*")
    ing_rows = extract_rows(ing_lines, 10, r"^(\d{3,5})\s+\S.*")
    desp_cap = aggregate(desp_rows, 0, 2, 4)
    ing_cap = aggregate(ing_rows, 0, 2, 6)
    return desp_cap, ing_cap

ROM_LABELS = [
    ("fons_liquids", r"^1\.\s*\(\+\)\s*Fons líquids"),
    ("pendent_cobrar", r"^2\.\s*\(\+\)\s*Drets pendents de cobrament"),
    ("pendent_pagar", r"^3\.\s*\(-\)\s*Obligacions pendents de pagament"),
    ("partides_pendents_aplicacio", r"^4\.\s*\(\+\)\s*Partides pendents d.aplicaci"),
    ("total", r"^I\.\s*Romanent de tresoreria total"),
    ("saldos_dubtos_cobrament", r"^II\.\s*Saldos de cobrament dubt"),
    ("exces_financament_afectat", r"^III\.\s*Exc.s de finançament afectat"),
    ("despeses_generals", r"^IV\.\s*Romanent de tresoreria per a despeses generals"),
]

def parse_romanent(path, year):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    start_i = None
    for i, l in enumerate(lines):
        if f"ROMANENT DE TRESORERIA a 31/12/{year}" in l:
            start_i = i
    if start_i is None:
        return None
    window = lines[start_i:start_i + 60]
    out = {}
    for field, pat in ROM_LABELS:
        for l in window:
            if re.match(pat, l.strip()):
                nums = re.findall(NUM, l)
                if nums:
                    out[field] = parse_num(nums[0])
                break
    return out

if __name__ == "__main__":
    desp, ing = parse_capitols(sys.argv[1])
    for c in sorted(desp):
        print("c" + c, desp[c])
    for c in sorted(ing):
        print("i" + c, ing[c])
    if len(sys.argv) > 2:
        print(parse_romanent(sys.argv[1], sys.argv[2]))
