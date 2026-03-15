from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="CSV API")

# Enable CORS for extramart.eu and all subdomains using regex
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9-]+\.)?extramart\.eu",
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Load CSV
csv_file = Path("data") / "sklady.csv"
df = pd.read_csv(csv_file, sep=";", dtype=str, keep_default_na=False)
df = df.replace({"": None})
df.set_index("code", inplace=True)

@app.get("/sklady/{code}")
def get_item(code: str):
    try:
        return df.loc[code].to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/sklady")
def get_items(pairCode: str = None, name: str = None, page: int = 1, limit: int = 100):
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
    """Simple health check"""
    return {"status": "ok", "rows_in_csv": len(df)}
