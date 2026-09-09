"""Extract text of EEA background note PDF + data-quality PDF from the EEA ETS zip (aviation pages)."""
import zipfile, subprocess, re, sys

Z = zipfile.ZipFile("/root/aviation-emissions/data/_eea_ets.zip")
PRE = "eea_t_eu-emission-trading-scheme_p_2005-2025_v02_r00/"
for name in ["ETC-CM_EEA EU ETS data viewer background note_July_2026.pdf",
             "ETC-CM EU-ETS data quality July_2026.pdf"]:
    src = PRE + name
    dst = "/tmp/" + name.replace(" ", "_")
    with open(dst, "wb") as f:
        f.write(Z.read(src))
    # extract text with pdfplumber or pypdf
    try:
        import pdfplumber
        with pdfplumber.open(dst) as pdf:
            txt = "\n".join((p.extract_text() or "") for p in pdf.pages)
        open(dst + ".txt", "w").write(txt)
        print(name, "-> extracted with pdfplumber", len(txt))
    except Exception as e:
        try:
            from pypdf import PdfReader
            txt = "\n".join((p.extract_text() or "") for p in PdfReader(dst).pages)
            open(dst + ".txt", "w").write(txt)
            print(name, "-> extracted with pypdf", len(txt))
        except Exception as e2:
            print(name, "EXTRACT FAIL", e, "|", e2)
            continue
    txt = open(dst + ".txt").read()
    print(f"  {len(txt)} chars")
    # print passages mentioning aviation allocation / correction
    for kw in ["1.2 Correction", "correction to freely", "2012", "ex-post", "Art 3", "3c"]:
        idxs = [m.start() for m in re.finditer(kw, txt, re.I)][:4]
        for i in idxs:
            snippet = txt[max(0, i-350):i+350].replace("\n", " ")
            snippet = re.sub(r"\s+", " ", snippet)
            print(f"\n### [{kw}] ...{snippet}...")
        print()
