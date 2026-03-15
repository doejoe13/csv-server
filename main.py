from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="CSV API")

# Enable CORS for extramart.eu and subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9-]+\.)?extramart\.eu",
    allow_methods=["GET"],
    allow_headers=["*"],
)

CSV_PATH = Path("./data/sklady.csv")

def load_csv():
    """Load CSV on each request to reflect hourly updates."""
    df = pd.read_csv(CSV_PATH, sep=";", dtype=str, keep_default_na=False)
    df = df.replace({"": None})
    df.set_index("code", inplace=True)
    return df

@app.get("/sklady/{code}")
def get_item(code: str):
    df = load_csv()
    try:
        return df.loc[code].to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/sklady")
def get_items(pairCode: str = None, name: str = None, page: int = 1, limit: int = 100):
    df = load_csv()
    filtered = df
    if pairCode:
        filtered = filtered[filtered["pairCode"] == pairCode]
    if name:
        filtered = filtered[filtered["name"] == name]

    start = (page - 1) * limit
    end = start + limit
    return filtered.reset_index().iloc[start:end].to_dict(orient="records")

@app.get("/health")
def healthcheck():
    df = load_csv()
    return {"status": "ok", "rows_in_csv": len(df)}
