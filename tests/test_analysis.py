import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "All_Diets.csv"
MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def load():
    return pd.read_csv(CSV)


def test_dataset_has_required_columns():
    df = load()
    for col in ["Diet_type", "Recipe_name", "Cuisine_type", *MACROS]:
        assert col in df.columns, f"missing column: {col}"


def test_dataset_not_empty():
    assert len(load()) > 0


def test_average_macros_are_non_negative():
    avg = load().groupby("Diet_type")[MACROS].mean()
    assert (avg.fillna(0) >= 0).all().all()


def test_analysis_script_runs():
    env = {**os.environ, "MPLBACKEND": "Agg"}  # no display in CI
    result = subprocess.run(
        [sys.executable, "data_analysis.py"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stderr