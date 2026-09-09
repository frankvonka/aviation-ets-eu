"""Extract the ETS database xlsx + README, inspect aviation rows."""
import zipfile, io
from pathlib import Path

Z = zipfile.ZipFile("/root/aviation-emissions/data/_eea_ets.zip")
PRE = "eea_t_eu-emission-trading-scheme_p_2005-2025_v02_r00/"
xlsx_path = "/root/aviation-emissions/data/ETS_Database_July_2026.xlsx"
with open(xlsx_path, "wb") as f:
    f.write(Z.read(PRE + "ETS_Database_July_2026.xlsx"))
print("readme:")
print(Z.read(PRE + "README.md").decode())

import openpyxl
wb = openpyxl.load_workbook(xlsx_path, read_only=True)
print("sheets:", wb.sheetnames)
