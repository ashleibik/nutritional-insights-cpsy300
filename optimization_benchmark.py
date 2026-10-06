"""
Task 5: Enhancement (data processing optimization)
CPSY-300 Project 1: Cloud-Native Nutritional Insights Application

Compares the original way we load and process All_Diets.csv against an
optimized version, and prints the time and memory difference.

Optimizations:
  1. usecols      : only read the 4 columns we actually need (skip recipe names, dates)
  2. dtypes       : float32 for macros instead of float64 (half the memory)
  3. category     : diet type stored as a category instead of repeated text
  4. clean once   : lowercase the few unique diet names, not all 7,800 rows
  5. observed=True: groupby only looks at categories that exist

Usage:
  python3 optimization_benchmark.py
  python3 optimization_benchmark.py path/to/All_Diets.csv
"""

import sys
import time
import tracemalloc
from datetime import datetime

import pandas as pd

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "All_Diets.csv"
MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]
RUNS = 20


def baseline(path):
    """Original approach (same as data_analysis.py / lambda_function.py)."""
    df = pd.read_csv(path)
    df["Diet_type"] = df["Diet_type"].astype(str).str.strip().str.lower()
    for col in MACROS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean(numeric_only=True))
    return df, df.groupby("Diet_type")[MACROS].mean()


def optimized(path):
    """Optimized approach."""
    df = pd.read_csv(
        path,
        usecols=["Diet_type"] + MACROS,
        dtype={"Diet_type": "category", **{c: "float32" for c in MACROS}},
    )
    # Clean only the unique category names (5 values) instead of every row
    clean = {c: str(c).strip().lower() for c in df["Diet_type"].cat.categories}
    df["Diet_type"] = df["Diet_type"].map(clean).astype("category")
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean())
    return df, df.groupby("Diet_type", observed=True)[MACROS].mean()


def measure(func):
    # Average time over several runs
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        df, result = func(CSV_PATH)
        times.append(time.perf_counter() - start)
    # Peak memory used while processing
    tracemalloc.start()
    df, result = func(CSV_PATH)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    df_mem = df.memory_usage(deep=True).sum()
    return sum(times) / len(times), peak, df_mem, result


def main():
    print(f"Benchmark run: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Dataset: {CSV_PATH}, averaged over {RUNS} runs\n")

    b_time, b_peak, b_mem, b_result = measure(baseline)
    o_time, o_peak, o_mem, o_result = measure(optimized)

    # Make sure the optimized version gives the same answers
    same = (b_result.round(1).values == o_result.astype("float64").round(1).values).all()

    rows = [
        ("Avg processing time", f"{b_time * 1000:.1f} ms", f"{o_time * 1000:.1f} ms", b_time / o_time),
        ("Peak memory used", f"{b_peak / 1024:.0f} KB", f"{o_peak / 1024:.0f} KB", b_peak / o_peak),
        ("DataFrame size", f"{b_mem / 1024:.0f} KB", f"{o_mem / 1024:.0f} KB", b_mem / o_mem),
    ]
    print(f"{'Metric':<22}{'Original':>12}{'Optimized':>12}{'Improvement':>14}")
    print("-" * 60)
    for name, before, after, factor in rows:
        print(f"{name:<22}{before:>12}{after:>12}{factor:>12.1f}x")
    print("-" * 60)
    print(f"Results match original: {'YES' if same else 'NO'}\n")
    print("Optimized averages per diet type:")
    print(o_result.astype("float64").round(2).to_string())


if __name__ == "__main__":
    main()
