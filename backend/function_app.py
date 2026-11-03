"""
Phase 2: HTTP triggered Azure Function
CPSY-300 Project: Cloud-Native Nutritional Insights Application

Same logic as Phase 1 (lambda_function.py), but instead of writing results.json
to disk, it answers an HTTP request with the results as JSON so the dashboard
can fetch them.

  GET /api/insights              -> all diet types
  GET /api/insights?diet=keto    -> only one diet type
"""

import io
import json
import logging
import os
import time
from datetime import datetime, timezone

import azure.functions as func
import pandas as pd
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

CONTAINER_NAME = os.getenv("DATA_CONTAINER", "datasets")
BLOB_NAME = os.getenv("DATA_BLOB", "All_Diets.csv")
MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def load_data():
    """Read the CSV from Blob Storage and clean it (same rules as Phase 1)."""
    conn = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    blob = BlobServiceClient.from_connection_string(conn).get_blob_client(
        container=CONTAINER_NAME, blob=BLOB_NAME
    )
    data = blob.download_blob().readall()

    df = pd.read_csv(io.BytesIO(data), usecols=["Diet_type", "Recipe_name", "Cuisine_type"] + MACROS)
    df["Diet_type"] = df["Diet_type"].astype(str).str.strip().str.lower()
    df["Cuisine_type"] = df["Cuisine_type"].astype(str).str.strip().str.lower()
    for col in MACROS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean())
    return df.drop_duplicates()


def build_insights(df, diet=None):
    """Turn the cleaned data into the JSON the dashboard uses."""
    if diet and diet.lower() != "all":
        df = df[df["Diet_type"] == diet.strip().lower()]

    avg = df.groupby("Diet_type")[MACROS].mean().round(2)
    counts = df.groupby("Diet_type").size()
    diets = [
        {
            "diet_type": name,
            "avg_protein_g": float(row["Protein(g)"]),
            "avg_carbs_g": float(row["Carbs(g)"]),
            "avg_fat_g": float(row["Fat(g)"]),
            "recipe_count": int(counts[name]),
        }
        for name, row in avg.iterrows()
    ]

    top = df.sort_values("Protein(g)", ascending=False).groupby("Diet_type").head(5)
    top_recipes = [
        {
            "diet_type": r["Diet_type"],
            "recipe": r["Recipe_name"],
            "cuisine": r["Cuisine_type"],
            "protein_g": round(float(r["Protein(g)"]), 2),
            "carbs_g": round(float(r["Carbs(g)"]), 2),
            "fat_g": round(float(r["Fat(g)"]), 2),
        }
        for _, r in top.iterrows()
    ]
    return {"diets": diets, "top_protein_recipes": top_recipes, "total_recipes": int(len(df))}


@app.route(route="insights", methods=["GET"])
def insights(req: func.HttpRequest) -> func.HttpResponse:
    start = time.perf_counter()
    diet = req.params.get("diet")
    try:
        result = build_insights(load_data(), diet)
    except Exception:
        logging.exception("Could not load or process the dataset")
        return func.HttpResponse(
            json.dumps({"error": "Could not load the dataset. Check the storage connection."}),
            status_code=500,
            mimetype="application/json",
        )

    result["metadata"] = {
        "filter": diet or "all",
        "execution_time_ms": round((time.perf_counter() - start) * 1000, 1),
        "processed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_blob": f"{CONTAINER_NAME}/{BLOB_NAME}",
    }
    return func.HttpResponse(json.dumps(result), mimetype="application/json")