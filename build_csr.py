import json, re
import pandas as pd

SRC = "/Users/siddharthlahri/Downloads/DynamicCSRReport (4).xlsx"
DIST_MAP = {
    "East Singhbum": "East Singhbhum",
    "Sahebganj": "Sahibganj",
    "Saraikela Kharsawan": "Saraikela-Kharsawan",
}
DROP = {"District Not Classified Elsewhere"}

df = pd.read_excel(SRC, sheet_name="sheet1", header=0)
df["List of Districts"] = df["List of Districts"].replace(DIST_MAP)
df = df[~df["List of Districts"].isin(DROP)]

year_cols = [c for c in df.columns if c.startswith("CSR Spent as on FY")]
year_of = lambda col: re.search(r"FY (\d{4}-\d{2})", col).group(1)

model = json.load(open("model.json"))
canon = set(model["canon"])

csr_totals = {d: {} for d in canon}
csr_domain = {d: {} for d in canon}
missing = set()

for _, row in df.iterrows():
    d = row["List of Districts"]
    if d not in canon:
        missing.add(d)
        continue
    sector = row["Development Sector"]
    for col in year_cols:
        y = year_of(col)
        cr = row[col]
        if pd.isna(cr):
            cr = 0
        rupees = round(cr * 1e7)
        csr_totals[d][y] = csr_totals[d].get(y, 0) + rupees
        csr_domain[d].setdefault(y, {})
        csr_domain[d][y][sector] = csr_domain[d][y].get(sector, 0) + rupees

if missing:
    print("WARNING: unmapped districts skipped:", missing)

years_sorted = sorted({year_of(c) for c in year_cols}, reverse=True)
model["years"] = years_sorted

domain_totals = {}
for d in csr_domain:
    for y in csr_domain[d]:
        for sec, v in csr_domain[d][y].items():
            domain_totals[sec] = domain_totals.get(sec, 0) + v
model["csrDomains"] = sorted(domain_totals, key=lambda s: -domain_totals[s])

for d in canon:
    model["districts"][d]["csr"] = csr_totals.get(d, {})
    model["districts"][d]["csrByDomain"] = csr_domain.get(d, {})

json.dump(model, open("model.json", "w"), separators=(",", ":"))
print("years:", years_sorted)
print("domains:", model["csrDomains"])
print("districts updated:", len(canon))
