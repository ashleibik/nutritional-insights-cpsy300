"""
Uploads All_Diets.csv to the Azurite Blob Storage emulator (container: datasets).
Use this if Azure Storage Explorer isn't available on your VM.

Usage:
  python3 upload_to_azurite.py                 # uploads ./All_Diets.csv
  python3 upload_to_azurite.py path/to/file.csv
"""

import sys

from lambda_function import CONTAINER_NAME, get_blob_service, upload_to_blob

path = sys.argv[1] if len(sys.argv) > 1 else "All_Diets.csv"
upload_to_blob(path)

print(f"\nBlobs in '{CONTAINER_NAME}':")
container = get_blob_service().get_container_client(CONTAINER_NAME)
for b in container.list_blobs():
    print(f"  {b.name}  ({b.size:,} bytes, modified {b.last_modified})")
