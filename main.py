from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import time

app = FastAPI(title="CSV API")

# Allow wellnet.sk and its subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9-]+\.)?wellnet\.sk",
    allow_methods=["GET"],
    allow_headers=["*"],
)

CSV_PATH = Path("/home/csv-server/data/sklady.csv")

df = None
last_load = 0
RELOAD_INTERVAL = 3600  # seconds (1 hour)


def load_csv():
    global df, last_load

    df = pd.read_csv(CSV_PATH, sep=";", dtype=str, keep_default_na=False)

    # Replace empty strings with None
    df = df.replace({"": None})

    # Convert column names like stock:wellnet -> stock-wellnet
    df.columns = df.columns.str.replace(":", "-", regex=False)

    # Set index
    df.set_index("code", inplace=True)

    last_load = time.time()


def get_df():
    global df, last_load

    if df is None or time.time() - last_load > RELOAD_INTERVAL:
        load_csv()

    return df


@app.get("/sklady/{code}")
def get_item(code: str):
    df_local = get_df()
    try:
        return df_local.loc[code].to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/sklady")
def get_items(
    pairCode: str = None,
    name: str = None,
    page: int = 1,
    limit: int = 100
):
    df_local = get_df()

    filtered = df_local

    if pairCode:
        filtered = filtered[filtered["pairCode"] == pairCode]

    if name:
        filtered = filtered[filtered["name"] == name]

    start = (page - 1) * limit
    end = start + limit

    return filtered.reset_index().iloc[start:end].to_dict(orient="records")


@app.get("/health")
def healthcheck():
    df_local = get_df()
    return {
        "status": "ok",
        "rows_in_csv": len(df_local),
        "last_reload": last_load
    }
