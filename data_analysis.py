"""
Task 1: Dataset Analysis and Insights
CPSY-300 Project 1: Cloud-Native Nutritional Insights Application

Reads All_Diets.csv, cleans it, calculates nutritional insights per diet type,
and saves the results (CSV tables + chart images) into the outputs/ folder.

Usage:
    python data_analysis.py                  # looks for All_Diets.csv in this folder
    python data_analysis.py path/to/file.csv
"""

import os
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # no screen needed, so it also works inside Docker
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "All_Diets.csv"
OUTPUT_DIR = "outputs"
CHART_DIR = os.path.join(OUTPUT_DIR, "charts")
MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ------------------------------------------------------------
# 1. Load and clean the data
# ------------------------------------------------------------
def load_and_clean(path):
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")

    # Column names sometimes show up as "Protein (g)" instead of "Protein(g)"
    df.columns = [c.strip().replace(" (g)", "(g)") for c in df.columns]

    # Clean up text columns so "paleo" and "Paleo " count as the same diet
    df["Diet_type"] = df["Diet_type"].astype(str).str.strip().str.lower()
    df["Cuisine_type"] = df["Cuisine_type"].astype(str).str.strip().str.lower()
    df["Recipe_name"] = df["Recipe_name"].astype(str).str.strip()

    # Make sure macros are numbers (bad values become NaN)
    for col in MACROS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Handle missing values: fill empty macros with the column average
    missing_before = df[MACROS].isna().sum()
    print("\nMissing values before cleaning:")
    print(missing_before.to_string())
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean(numeric_only=True))
    print(f"Missing values after cleaning: {int(df[MACROS].isna().sum().sum())}")

    # Drop exact duplicate rows
    dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f"Removed {dupes} duplicate rows, {len(df)} rows left")

    return df


# ------------------------------------------------------------
# 2. Calculations
# ------------------------------------------------------------
def average_macros(df):
    return df.groupby("Diet_type")[MACROS].mean().round(2)


def top_protein_recipes(df, n=5):
    return (
        df.sort_values("Protein(g)", ascending=False)
        .groupby("Diet_type")
        .head(n)
        .sort_values(["Diet_type", "Protein(g)"], ascending=[True, False])
        [["Diet_type", "Recipe_name", "Cuisine_type", "Protein(g)"]]
    )


def highest_protein_diet(df):
    by_avg = df.groupby("Diet_type")["Protein(g)"].mean()
    by_total = df.groupby("Diet_type")["Protein(g)"].sum()
    return by_avg.idxmax(), by_avg.max(), by_total.idxmax(), by_total.max()


def common_cuisines(df, n=3):
    counts = (
        df.groupby(["Diet_type", "Cuisine_type"])
        .size()
        .reset_index(name="Recipe_count")
        .sort_values(["Diet_type", "Recipe_count"], ascending=[True, False])
    )
    return counts.groupby("Diet_type").head(n)


def add_ratios(df):
    # Replace 0 with NaN first so we never divide by zero
    carbs = df["Carbs(g)"].replace(0, float("nan"))
    fat = df["Fat(g)"].replace(0, float("nan"))
    df["Protein_to_Carbs_ratio"] = (df["Protein(g)"] / carbs).round(3)
    df["Carbs_to_Fat_ratio"] = (df["Carbs(g)"] / fat).round(3)
    return df


# ------------------------------------------------------------
# 3. Visualizations
# ------------------------------------------------------------
def plot_avg_macros_bar(avg):
    long = avg.reset_index().melt(id_vars="Diet_type", var_name="Macronutrient", value_name="Grams")
    plt.figure(figsize=(10, 6))
    sns.barplot(data=long, x="Diet_type", y="Grams", hue="Macronutrient")
    plt.title("Average Macronutrients by Diet Type")
    plt.xlabel("Diet Type")
    plt.ylabel("Average Amount (g)")
    plt.legend(title="Macronutrient", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    path = os.path.join(CHART_DIR, "bar_avg_macros.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_heatmap(avg):
    plt.figure(figsize=(8, 6))
    sns.heatmap(avg, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.5)
    plt.title("Average Macronutrient Content by Diet Type")
    plt.xlabel("Macronutrient")
    plt.ylabel("Diet Type")
    plt.tight_layout()
    path = os.path.join(CHART_DIR, "heatmap_macros.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_top_protein_scatter(top):
    plt.figure(figsize=(11, 6))
    sns.scatterplot(data=top, x="Cuisine_type", y="Protein(g)", hue="Diet_type", s=120)
    plt.title("Top 5 Protein Rich Recipes per Diet Type by Cuisine")
    plt.xlabel("Cuisine Type")
    plt.ylabel("Protein (g)")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Diet Type", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    path = os.path.join(CHART_DIR, "scatter_top_protein.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    print(f"Run started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    os.makedirs(CHART_DIR, exist_ok=True)

    section("1. Load and clean data")
    df = load_and_clean(CSV_PATH)

    section("2. Average macronutrients per diet type")
    avg = average_macros(df)
    print(avg.to_string())

    section("3. Top 5 protein rich recipes per diet type")
    top = top_protein_recipes(df)
    print(top.to_string(index=False))

    section("4. Diet type with the highest protein")
    avg_diet, avg_val, total_diet, total_val = highest_protein_diet(df)
    print(f"Highest average protein per recipe: {avg_diet} ({avg_val:.2f} g)")
    print(f"Highest total protein across all recipes: {total_diet} ({total_val:.2f} g)")

    section("5. Most common cuisines per diet type")
    cuisines = common_cuisines(df)
    print(cuisines.to_string(index=False))

    section("6. New metrics: Protein to Carbs and Carbs to Fat ratios")
    df = add_ratios(df)
    print(df[["Diet_type", "Recipe_name", "Protein_to_Carbs_ratio", "Carbs_to_Fat_ratio"]]
          .head(10).to_string(index=False))

    section("7. Saving results")
    avg.to_csv(os.path.join(OUTPUT_DIR, "avg_macros_by_diet.csv"))
    top.to_csv(os.path.join(OUTPUT_DIR, "top5_protein_recipes.csv"), index=False)
    cuisines.to_csv(os.path.join(OUTPUT_DIR, "common_cuisines_by_diet.csv"), index=False)
    df.to_csv(os.path.join(OUTPUT_DIR, "all_diets_cleaned_with_ratios.csv"), index=False)
    for chart in (plot_avg_macros_bar(avg), plot_heatmap(avg), plot_top_protein_scatter(top)):
        print(f"Saved chart: {chart}")

    print(f"\nRun finished: {datetime.now():%Y-%m-%d %H:%M:%S}")


if __name__ == "__main__":
    main()
