# tool/src/data.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

from .schema import REQUIRED

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "analytics"

def _read_csv_safely(path: Path) -> pd.DataFrame:
    # Prova UTF-8, poi fallback (per i file con Ã che abbiamo visto)
    try:
        return pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1", low_memory=False)

def _validate(df: pd.DataFrame, filename: str) -> None:
    required = REQUIRED.get(filename, [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[{filename}] Colonne mancanti: {missing}")

@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    datasets = {}
    for filename in REQUIRED.keys():
        path = DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"File non trovato: {path}")
        df = _read_csv_safely(path)

        # Normalizzazioni leggere (sicure)
        if "codice_cliente" in df.columns:
            df["codice_cliente"] = pd.to_numeric(df["codice_cliente"], errors="coerce").astype("Int64")

        _validate(df, filename)
        datasets[filename] = df

    return datasets

def get_df(name: str) -> pd.DataFrame:
    return load_all()[name]
