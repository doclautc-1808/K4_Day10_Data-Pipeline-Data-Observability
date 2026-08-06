from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import compact_join, normalize_whitespace, read_json, write_csv, write_json
from ingestion.cleaning import clean_text


def repair_dataset(
    df: pd.DataFrame | None = None,
    settings: Settings | None = None,
    input_path: Path | str | None = None,
    output_path: Path | str | None = None,
) -> pd.DataFrame:
    """Quality Gate Filter & Repair Pipeline:
    1. Clean HTML / JATS XML tags & whitespace from titles and summaries.
    2. Filter out NULL / missing title or summary, or summary < 50 chars.
    3. Drop duplicate DOIs (paper_id) and duplicate titles.
    4. Filter out outdated / stale data (age_days > freshness_threshold_days).
    5. Rebuild text_for_embedding.
    6. Save to data/repaired/repaired_papers.json.
    """
    if df is None:
        src_path = Path(input_path) if input_path else Path("data/corrupted/corrupted_papers.json")
        if not src_path.exists():
            src_path = Path("data/raw/crossref_records.json")
        if not src_path.exists():
            raise FileNotFoundError(f"Input file not found at {src_path}")
        records = read_json(src_path)
        df = pd.DataFrame(records)

    if df.empty:
        return df

    threshold = settings.freshness_threshold_days if settings else 180
    now_date = datetime.now(UTC).date()

    repaired_rows = []
    for _, row in df.iterrows():
        paper_id = str(row.get("paper_id", "")).strip()
        title = clean_text(str(row.get("title", "")))
        summary = clean_text(str(row.get("summary", "")))

        # Quality Gate 1: Remove NULL / missing critical fields or summary < 50 chars
        if not paper_id or not title or not summary or len(summary) < 50:
            continue

        # Quality Gate 2: Clean authors & categories
        authors_val = row.get("authors")
        if isinstance(authors_val, list):
            authors = [clean_text(str(a)) for a in authors_val if clean_text(str(a))]
        else:
            authors = [clean_text(str(authors_val))] if authors_val else []
        if not authors:
            authors = ["Unknown Author"]
        authors_joined = compact_join(authors, sep=", ")

        categories_val = row.get("categories")
        if isinstance(categories_val, list):
            categories = [clean_text(str(c)) for c in categories_val if clean_text(str(c))]
        else:
            categories = [clean_text(str(categories_val))] if categories_val else []
        if not categories:
            categories = ["cs.AI"]
        primary_category = categories[0]
        categories_joined = compact_join(categories, sep=", ")

        published = str(row.get("published", row.get("published_date", "")))
        try:
            pub_dt = datetime.strptime(published[:10], "%Y-%m-%d").date()
        except ValueError:
            pub_dt = now_date

        age_days = (now_date - pub_dt).days
        if age_days < 0:
            age_days = 0

        # Quality Gate 3: Filter out outdated / stale data
        if age_days > threshold:
            continue

        updated = str(row.get("updated", published))
        abs_url = str(row.get("abs_url", f"https://doi.org/{paper_id}"))
        pdf_url = str(row.get("pdf_url", abs_url))
        comment = str(row.get("comment", ""))

        # Rebuild text_for_embedding
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Summary: {summary}"
        )

        repaired_rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": primary_category,
                "published": published,
                "published_date": published,
                "updated": updated,
                "age_days": age_days,
                "summary_chars": len(summary),
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
                "text_for_embedding": text_for_embedding,
            }
        )

    repaired_df = pd.DataFrame(repaired_rows)
    if not repaired_df.empty:
        # Quality Gate 4: Drop duplicates (paper_id & title)
        repaired_df = repaired_df.drop_duplicates(subset=["paper_id"]).reset_index(drop=True)
        repaired_df = repaired_df.drop_duplicates(subset=["title"]).reset_index(drop=True)
        repaired_df = repaired_df.sort_values(by="published", ascending=False).reset_index(drop=True)

    repaired_json = repaired_df.to_dict(orient="records")

    target_out = Path(output_path) if output_path else Path("data/repaired/repaired_papers.json")
    write_json(target_out, repaired_json)

    alt_path1 = Path("data/repaired/repaired_papers.json")
    if alt_path1 != target_out:
        write_json(alt_path1, repaired_json)

    if settings:
        write_json(settings.paths.repaired_clean_json, repaired_json)
        write_csv(repaired_df, settings.paths.repaired_clean_csv)

    return repaired_df
