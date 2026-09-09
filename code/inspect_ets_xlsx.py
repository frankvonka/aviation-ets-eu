"""Inspect the ETS Database xlsx: dimensions, headers, aviation sample rows."""
import openpyxl
from pathlib import Path

wb = openpyxl.load_workbook("/root/aviation-emissions/data/ETS_Database_July_2026.xlsx", read_only=True)
ws = wb["Sheet1"]
print("dims:", ws.max_row, "x", ws.max_column)
rows = ws.iter_rows(min_row=1, max_row=6, values_only=True)
for i, row in enumerate(rows, 1):
    print(f"row{i}:", [str(c)[:30] if c is not None else "" for c in row])
wb.close()
