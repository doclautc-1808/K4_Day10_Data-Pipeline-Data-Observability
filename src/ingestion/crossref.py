from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"
RETRY_STATUS_CODES = {429, 503}
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 1.0


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return normalize_whitespace(_strip_html(value))


def _parse_author(author: dict) -> str:
    if literal := author.get("literal"):
        return normalize_whitespace(str(literal))
    given = normalize_whitespace(str(author.get("given", "")))
    family = normalize_whitespace(str(author.get("family", "")))
    if given and family:
        return f"{given} {family}"
    return given or family


def _parse_date(date_object: dict | None) -> str:
    if not date_object:
        return ""
    date_parts = date_object.get("date-parts") or []
    if not date_parts or not isinstance(date_parts[0], list):
        return ""
    parts = [str(int(x)) for x in date_parts[0] if x is not None]
    return "-".join(parts)


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = _normalize_text(item.get("DOI", ""))
        title = _normalize_text((item.get("title") or [""])[0])
        summary = _normalize_text(item.get("abstract", ""))
        if not summary:
            raw_description = item.get("description", "")
            if isinstance(raw_description, list):
                raw_description = raw_description[0] if raw_description else ""
            summary = _normalize_text(raw_description)
        if not summary:
            summary = _normalize_text(item.get("subtitle", ""))

        authors_raw = item.get("author", [])
        authors = [_parse_author(author) for author in authors_raw if isinstance(author, dict)]
        authors = [author for author in authors if author]

        categories = [normalize_whitespace(str(subject)) for subject in item.get("subject", []) if subject]
        primary_category = categories[0] if categories else _normalize_text(item.get("type", ""))

        published = _parse_date(
            item.get("published-print")
            or item.get("published-online")
            or item.get("published")
            or item.get("issued")
            or item.get("created")
        )
        updated = _parse_date(item.get("created") or item.get("issued") or item.get("published-online") or item.get("published-print"))

        abs_url = _normalize_text(item.get("URL", ""))
        pdf_url = ""
        for link in item.get("link", []):
            if not isinstance(link, dict):
                continue
            if link.get("content-type", "").lower() == "application/pdf":
                pdf_url = _normalize_text(link.get("URL", ""))
                break
        if not pdf_url and doi:
            pdf_url = f"https://doi.org/{doi}"

        comment = _normalize_text(item.get("publisher", ""))

        if not doi or not title or not summary:
            continue

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def _request_with_retry(url: str, params: dict[str, str]) -> dict:
    session = requests.Session()
    for attempt in range(1, MAX_RETRIES + 1):
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
            sleep_seconds = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            time.sleep(sleep_seconds)
            continue
        response.raise_for_status()
    raise RuntimeError(f"Crossref API failed after {MAX_RETRIES} retries.")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": str(settings.max_results),
        "sort": "relevance",
        "order": "desc",
    }

    payload = _request_with_retry(CROSSREF_API_URL, params)
    ensure_parent(settings.paths.raw_api_response)
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    ensure_parent(settings.paths.raw_records_json)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of records in {path}")

    records: list[PaperRecord] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        records.append(
            PaperRecord(
                paper_id=str(raw.get("paper_id", "")),
                title=str(raw.get("title", "")),
                summary=str(raw.get("summary", "")),
                authors=[str(author) for author in raw.get("authors", []) if author],
                categories=[str(category) for category in raw.get("categories", []) if category],
                primary_category=str(raw.get("primary_category", "")),
                published=str(raw.get("published", "")),
                updated=str(raw.get("updated", "")),
                abs_url=str(raw.get("abs_url", "")),
                pdf_url=str(raw.get("pdf_url", "")),
                comment=str(raw.get("comment", "")),
            )
        )
    return records
