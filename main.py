
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
import os
from pathlib import Path

app = FastAPI(title="CSV API")

# Allow extramart.eu and subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-zA-Z0-9-]+\.)?extramart\.eu",
    allow_methods=["GET"],
    allow_headers=["*"],
)

csv_file = Path("data") / "sklady.csv"

data = {}
rows = []
last_file_mtime = 0


def load_csv():
    global data, rows, last_file_mtime

    new_data = {}
    new_rows = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:

            for k, v in row.items():
                if v == "":
                    row[k] = None

            code = row.get("code")

            if code:
                new_data[code] = row

            new_rows.append(row)

    data = new_data
    rows = new_rows
    last_file_mtime = os.path.getmtime(csv_file)


def ensure_loaded():
    global last_file_mtime

    file_mtime = os.path.getmtime(csv_file)

    if not data or file_mtime != last_file_mtime:
        load_csv()


@app.get("/health")
def health():
    """
    Healthcheck endpoint
    Used by Docker / Dokploy
    """
    try:
        if not csv_file.exists():
            return {"status": "error", "reason": "csv_missing"}

        ensure_loaded()

        return {
            "status": "ok",
            "rows": len(rows),
            "csv": str(csv_file)
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }


@app.get("/sklady/{code}")
def get_item(code: str):

    ensure_loaded()

    item = data.get(code)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@app.get("/sklady")
def get_items(page: int = 1, limit: int = 100):

    ensure_loaded()

    start = (page - 1) * limit
    end = start + limit

    return rows[start:end]
