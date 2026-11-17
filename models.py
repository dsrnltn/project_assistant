import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"

def _read(name):
    p = DATA / name
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, dtype=str, keep_default_na=False)

def _write(df, name):
    (DATA / name).parent.mkdir(exist_ok=True)
    df.to_csv(DATA / name, index=False, encoding="utf-8")

def load_equipment():
    return _read("equipment.csv")

def load_characteristics():
    return _read("characteristics.csv")

def load_spec_items():
    return _read("spec_items.csv")

def load_spec_values():
    return _read("spec_values.csv")

def save_spec_items(df):
    _write(df, "spec_items.csv")

def save_spec_values(df):
    _write(df, "spec_values.csv")

def next_id(df, col="id"):
    if df.empty:
        return "1"
    return str(int(df[col].astype(int).max()) + 1)