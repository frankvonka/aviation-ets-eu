#!/usr/bin/env python3
"""Final validation of both target files + convenience CSV extract."""
import pyarrow.parquet as pq, csv, collections, os, zipfile, re

D = "/root/aviation-emissions/data"

# ---- 1) g2g_emissions.csv physical sanity ----
t = pq.ParquetFile(f"{D}/g2g_emissions.parquet").read()
lv = t.column("LEVEL").to_pylist()
ar = t.column("AREA").to_pylist()
yr = t.column("YEAR").to_pylist()
mo = t.column("MONTH").to_pylist()
co2 = t.column("CO2_TONS").to_pylist()
ecac = collections.Counter()
for l, a, y, m, c in zip(lv, ar, yr, mo, co2):
    if l == "NETWORK" and a == "ECAC":
        ecac[(int(y), int(m))] += c or 0
for ym in [(2019, 5), (2019, 12), (2020, 5), (2021, 5), (2022, 5), (2024, 12)]:
    print(f"ECAC network CO2 {ym[0]}-{ym[1]:02d}: {ecac[ym]/1e6:8.2f} Mt")
grid = {(int(y), int(m)) for y, m in zip(yr, mo)}
print("g2g: rows", t.num_rows, "| distinct year-month:", len(grid),
      "| span", f"{min(grid)[0]}-{min(grid)[1]:02d}", "→", f"{max(grid)[0]}-{max(grid)[1]:02d}")
print("focus types:", collections.Counter(t.column('FOCUS_TYPE').to_pylist()))

# verify CSV on disk matches parquet row count
with open(f"{D}/g2g_emissions.csv") as f:
    n = sum(1 for _ in f)
print("g2g_emissions.csv lines:", n, "(expect", t.num_rows + 1, ")")

# ---- 2) xlsx DATA sheet -> CSV extract ----
z = zipfile.ZipFile(f"{D}/CO2_emissions_by_state.xlsx")
ss_xml = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
sst = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<si>(.*?)</si>", ss_xml, re.S)]
xml = z.read("xl/worksheets/sheet3.xml").decode("utf-8", "replace")
rows_out, header = [], None
for rm in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
    cells = {}
    for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"(?:[^>]*?t="(\w+)")?[^>]*>(?:<v>([^<]*)</v>)?(?:<is><t[^>]*>([^<]*)</t></is>)?</c>', rm):
        col, _, typ, v, inline = cm.groups()
        cells[col] = sst[int(v)] if typ == "s" and v is not None else (inline or v)
    if header is None:
        header = [cells.get(c) for c in "ABCDEF"]
        continue
    rows_out.append([cells.get(c) for c in "ABCDEF"])
with open(f"{D}/CO2_emissions_by_state_DATA.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows_out)
yrs = sorted({int(float(r[0])) for r in rows_out})
print(f"\nxlsx extract: {len(rows_out)} rows | years {yrs[0]}-{yrs[-1]} | header {header}")

# ---- 3) quarantine stale junk ----
os.makedirs(f"{D}/_stale_attempts", exist_ok=True)
for name in ["g2g_test.csv", "emissions_test.csv", "g2g_jina.txt"]:
    src = f"{D}/{name}"
    if os.path.exists(src):
        os.replace(src, f"{D}/_stale_attempts/{name}")
        print("quarantined:", name)
for p in [".wayback_discover.py", ".cdx_probe.py", ".cdx_hunt.py", ".wb_fetch.py",
          ".hunt2.py", ".xlsx_peek.py", ".wayback_discovery.json", ".cdx_hits.json", ".cdx_hunt2.json"]:
    if os.path.exists(f"{D}/{p}"):
        os.replace(f"{D}/{p}", f"{D}/_stale_attempts/{p}")
print("done")
