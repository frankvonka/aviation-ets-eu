#!/usr/bin/env python3
"""Parse the Small Emitters Tool xlsx DATA/META sheets without openpyxl."""
import zipfile, re, collections

P = "/root/aviation-emissions/data/CO2_emissions_by_state.xlsx"
z = zipfile.ZipFile(P)

# map sheet name -> file via workbook.xml + rels
wb = z.read("xl/workbook.xml").decode("utf-8", "replace")
rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8", "replace")
rid2target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
sheets = re.findall(r'<sheet[^>]*name="([^"]+)"[^>]*r:id="(rId\d+)"', wb)
sheetfile = {name: "xl/" + rid2target[rid].lstrip("/") for name, rid in sheets if rid in rid2target}
print("sheet map:", sheetfile)

ss_xml = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
sst = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<si>(.*?)</si>", ss_xml, re.S)]

def parse_sheet(path, max_rows=None):
    xml = z.read(path).decode("utf-8", "replace")
    rows = []
    for rm in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"(?:[^>]*?t="(\w+)")?[^>]*>(?:<v>([^<]*)</v>)?(?:<is><t[^>]*>([^<]*)</t></is>)?</c>', rm):
            col, _rownum, typ, v, inline = cm.groups()
            if typ == "s" and v is not None:
                val = sst[int(v)]
            elif inline:
                val = inline
            else:
                val = v
            cells[col] = val
        rows.append(cells)
        if max_rows and len(rows) >= max_rows:
            break
    return rows

for name in ("META", "DATA"):
    if name not in sheetfile:
        continue
    rows = parse_sheet(sheetfile[name])
    print(f"\n===== {name}: {len(rows)} rows =====")
    for r in rows[:6]:
        print("  ", dict(sorted(r.items())))

# DATA sheet column analysis
if "DATA" in sheetfile:
    rows = parse_sheet(sheetfile["DATA"])
    hdr = rows[0]
    cols = sorted(hdr.keys(), key=lambda c: (len(c), c))
    print("\nDATA header:", [hdr[c] for c in cols])
    data = [{hdr.get(c, c): r.get(c) for c in cols} for r in rows[1:] if r]
    yrs = collections.Counter(d.get("YEAR") for d in data)
    print("rows:", len(data))
    try:
        yv = sorted({int(float(y)) for y in yrs if y})
        print("years:", yv[0], "-", yv[-1], "| distinct:", len(yv))
    except Exception as e:
        print("year parse:", e, list(yrs)[:8])
    sts = {d.get("STATE_NAME") for d in data}
    print("distinct states:", len(sts))
    ms = {d.get("MONTH") for d in data}
    print("distinct months:", len(ms), sorted(ms)[:14])
    print("sample:", data[0], data[-1])
