from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="CSV API")

# Enable CORS for all origins (so JS can fetch from any page)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow JavaScript from any domain
    allow_methods=["GET"], # only allow GET requests
    allow_headers=["*"],   # allow all headers
)

# Load CSV
csv_file = Path("data") / "sklady.csv"
df = pd.read_csv(csv_file, sep=";", dtype=str, keep_default_na=False)
df = df.replace({"": None})  # empty cells -> None
df.set_index("code", inplace=True)

@app.get("/sklady/{code}")
def get_item(code: str):
    """Return a single row by code"""
    try:
        return df.loc[code].to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/sklady")
def get_items(
    pairCode: str = None,
    name: str = None,
    page: int = 1,
    limit: int = 100
):
    """Return multiple rows with optional filters and pagination"""
    filtered = df
    if pairCode:
        filtered = filtered[filtered["pairCode"] == pairCode]
    if name:
        filtered = filtered[filtered["name"] == name]

    start = (page - 1) * limit
    end = start + limit
    return filtered.reset_index().iloc[start:end].to_dict(orient="records")

