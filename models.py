import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"

def _read(name):
    p = DATA / name
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, dtype=str, keep_default_na=False, sep=";",
                       encoding="utf-8-sig")

def load_equipment():
    return _read("equipment.csv")

def load_characteristics():
    df = _read("characteristics.csv")
    if not df.empty and "по_умолчанию" not in df.columns:
        df["по_умолчанию"] = ""
    return df