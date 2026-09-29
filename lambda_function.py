"""
Task 3: Cloud-Native Data Processing with Serverless Functions (simulated)
CPSY-300 Project 1: Cloud-Native Nutritional Insights Application

Simulates an Azure Function that:
  1. Reads All_Diets.csv from Azure Blob Storage (Azurite emulator running locally)
  2. Calculates average protein, carbs and fat per diet type
  3. Saves the results to a simulated NoSQL database (simulated_nosql/results.json)

Usage:
  python3 lambda_function.py            # run the function once (manual invoke)
  python3 lambda_function.py --watch    # event mode: drop a CSV in incoming/ and it
                                        # gets uploaded to Azurite and processed automatically
"""

import io
import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

# Azurite's default local connection string. This account and key are public,
# built into Azurite for local development only. They are not real secrets.
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", AZURITE_CONNECTION_STRING)

CONTAINER_NAME = "datasets"
BLOB_NAME = "All_Diets.csv"
NOSQL_DIR = "simulated_nosql"
NOSQL_FILE = os.path.join(NOSQL_DIR, "results.json")
WATCH_DIR = "incoming"
MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}")


def get_blob_service():
    return BlobServiceClient.from_connection_string(CONNECTION_STRING)


def upload_to_blob(local_path, blob_name=BLOB_NAME):
    """Upload a local file to the Azurite 'datasets' container."""
    service = get_blob_service()
    try:
        service.create_container(CONTAINER_NAME)
        log(f"Created container '{CONTAINER_NAME}'")
    except ResourceExistsError:
        pass
    blob = service.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    with open(local_path, "rb") as f:
        blob.upload_blob(f, overwrite=True)
    log(f"Uploaded {local_path} to blob {CONTAINER_NAME}/{blob_name}")


def process_nutritional_data_from_azurite(blob_name=BLOB_NAME):
    """The 'serverless function': read CSV from blob, calculate, save to NoSQL."""
    start = time.perf_counter()
    log(f"Function triggered for blob {CONTAINER_NAME}/{blob_name}")

    # 1. Read the CSV straight from Azurite Blob Storage
    blob = get_blob_service().get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    data = blob.download_blob().readall()
    df = pd.read_csv(io.BytesIO(data))
    log(f"Downloaded {len(data):,} bytes, {len(df):,} rows from Azurite")

    # 2. Light cleaning (same rules as data_analysis.py)
    df.columns = [c.strip().replace(" (g)", "(g)") for c in df.columns]
    df["Diet_type"] = df["Diet_type"].astype(str).str.strip().str.lower()
    for col in MACROS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean(numeric_only=True))

    # 3. Calculate average macros per diet type
    avg = df.groupby("Diet_type")[MACROS].mean().round(2)
    counts = df.groupby("Diet_type").size()

    # 4. Save to the simulated NoSQL database (one JSON document per diet type,
    #    shaped like Cosmos DB documents with an id field)
    processed_at = datetime.now().isoformat(timespec="seconds")
    documents = [
        {
            "id": diet,
            "Diet_type": diet,
            "avg_protein_g": row["Protein(g)"],
            "avg_carbs_g": row["Carbs(g)"],
            "avg_fat_g": row["Fat(g)"],
            "recipe_count": int(counts[diet]),
            "source_blob": f"{CONTAINER_NAME}/{blob_name}",
            "processed_at": processed_at,
        }
        for diet, row in avg.iterrows()
    ]
    os.makedirs(NOSQL_DIR, exist_ok=True)
    with open(NOSQL_FILE, "w") as f:
        json.dump(documents, f, indent=2)

    print(avg.to_string())
    log(f"Saved {len(documents)} documents to {NOSQL_FILE}")
    log(f"Function finished in {time.perf_counter() - start:.2f}s")
    return "Data processed and stored successfully."


def watch_folder():
    """Simulate an event trigger: new CSV in incoming/ -> upload -> run function."""
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class NewCsvHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory or not event.src_path.lower().endswith(".csv"):
                return
            time.sleep(1)  # give the copy a second to finish
            log(f"Event: new file detected {event.src_path}")
            upload_to_blob(event.src_path)
            print(process_nutritional_data_from_azurite())

    os.makedirs(WATCH_DIR, exist_ok=True)
    observer = Observer()
    observer.schedule(NewCsvHandler(), WATCH_DIR, recursive=False)
    observer.start()
    log(f"Watching '{WATCH_DIR}/' for new CSV files (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch_folder()
    else:
        print(process_nutritional_data_from_azurite())
