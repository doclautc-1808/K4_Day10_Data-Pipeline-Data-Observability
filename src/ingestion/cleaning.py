from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    df = pd.DataFrame([vars(r) for r in records])
    
    if df.empty:
        return df

    # Normalize text
    df["title"] = df["title"].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["summary"] = df["summary"].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    # Remove HTML tags from abstract/summary
    df["summary"] = df["summary"].apply(lambda x: re.sub(r'<[^>]+>', '', x))
    
    # Parse published date
    df["published"] = pd.to_datetime(df["published"], errors="coerce")
    
    # Tinh age_days
    if df["published"].dt.tz is not None:
        df["published"] = df["published"].dt.tz_localize(None)
    run_date_naive = run_date.replace(tzinfo=None) if run_date.tzinfo else run_date
    df["age_days"] = (run_date_naive - df["published"]).dt.days
    df["age_days"] = df["age_days"].fillna(-1).astype(int)
    
    # Tao helper columns
    df["authors_joined"] = df["authors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["categories_joined"] = df["categories"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = "Title: " + df["title"] + "\nAuthors: " + df["authors_joined"] + "\nAbstract: " + df["summary"]
    
    # Drop duplicates and invalid rows
    df = df.drop_duplicates(subset=["paper_id"])
    df = df[df["title"] != ""]
    df = df[df["summary"] != ""]
    
    # Sort
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    
    # Format published date back to string
    df["published"] = df["published"].dt.strftime("%Y-%m-%dT%H:%M:%S").fillna("")
    
    return df
