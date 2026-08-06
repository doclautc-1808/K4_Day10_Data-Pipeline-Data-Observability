from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


MIN_SUMMARY_CHARS = 50


def _blank_mask(series: pd.Series) -> pd.Series:
    """Return a mask that treats nulls and whitespace-only values as missing."""
    return series.isna() | series.astype(str).str.strip().eq("")


def _check(
    name: str,
    dimension: str,
    success: bool,
    observed_value: Any,
    expectation: str,
    details: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "dimension": dimension,
        "success": bool(success),
        "observed_value": observed_value,
        "expectation": expectation,
        "details": details,
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run auditable quality checks and persist their JSON result.

    A missing required column is reported as a failed check instead of raising
    immediately. This makes the quality artifact useful when a pipeline stage
    produces an incomplete schema.
    """
    total_rows = int(len(df))
    checks: list[dict[str, Any]] = []

    checks.append(
        _check(
            "row_count_positive",
            "volume",
            total_rows > 0,
            total_rows,
            "row count must be greater than 0",
        )
    )

    required_columns = ["paper_id", "title", "summary", "published", "age_days", "text_for_embedding"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    checks.append(
        _check(
            "required_columns_present",
            "schema",
            not missing_columns,
            missing_columns,
            f"all required columns must exist: {', '.join(required_columns)}",
        )
    )

    if "paper_id" in df.columns:
        missing_ids = int(_blank_mask(df["paper_id"]).sum())
        normalized_ids = df["paper_id"].fillna("").astype(str).str.strip().str.lower()
        duplicate_ids = int(normalized_ids[normalized_ids.ne("")].duplicated(keep=False).sum())
        checks.extend(
            [
                _check(
                    "paper_id_not_null",
                    "completeness",
                    missing_ids == 0,
                    missing_ids,
                    "missing or blank paper_id count must equal 0",
                ),
                _check(
                    "paper_id_unique",
                    "uniqueness",
                    duplicate_ids == 0,
                    duplicate_ids,
                    "rows participating in duplicate paper_id groups must equal 0",
                    "Comparison is case-insensitive and ignores surrounding whitespace.",
                ),
            ]
        )
    else:
        checks.extend(
            [
                _check("paper_id_not_null", "completeness", False, None, "paper_id column must exist"),
                _check("paper_id_unique", "uniqueness", False, None, "paper_id column must exist"),
            ]
        )

    for column in ("title", "summary", "text_for_embedding"):
        if column in df.columns:
            blank_rows = int(_blank_mask(df[column]).sum())
            checks.append(
                _check(
                    f"{column}_not_empty",
                    "completeness",
                    blank_rows == 0,
                    blank_rows,
                    f"missing or blank {column} count must equal 0",
                )
            )
        else:
            checks.append(
                _check(f"{column}_not_empty", "completeness", False, None, f"{column} column must exist")
            )

    if "summary" in df.columns:
        summary_lengths = df["summary"].fillna("").astype(str).str.strip().str.len()
        short_summaries = int((summary_lengths < MIN_SUMMARY_CHARS).sum())
        checks.append(
            _check(
                "summary_min_length",
                "validity",
                short_summaries == 0,
                short_summaries,
                f"every summary must contain at least {MIN_SUMMARY_CHARS} characters",
                f"minimum observed length: {int(summary_lengths.min()) if total_rows else 0}",
            )
        )
    else:
        checks.append(
            _check("summary_min_length", "validity", False, None, "summary column must exist")
        )

    if "published" in df.columns:
        published = pd.to_datetime(df["published"], errors="coerce", utc=True)
        invalid_dates = int(published.isna().sum())
        checks.append(
            _check(
                "published_date_valid",
                "validity",
                invalid_dates == 0,
                invalid_dates,
                "unparseable or missing published date count must equal 0",
            )
        )
    else:
        checks.append(
            _check("published_date_valid", "validity", False, None, "published column must exist")
        )

    if "age_days" in df.columns:
        ages = pd.to_numeric(df["age_days"], errors="coerce")
        invalid_ages = int((ages.isna() | (ages < 0)).sum())
        stale_rows = int((ages > settings.freshness_threshold_days).sum())
        checks.extend(
            [
                _check(
                    "age_days_valid",
                    "validity",
                    invalid_ages == 0,
                    invalid_ages,
                    "age_days must be a non-negative number for every row",
                ),
                _check(
                    "records_are_fresh",
                    "freshness",
                    stale_rows == 0,
                    stale_rows,
                    f"no row may exceed {settings.freshness_threshold_days} days",
                ),
            ]
        )
    else:
        checks.extend(
            [
                _check("age_days_valid", "validity", False, None, "age_days column must exist"),
                _check("records_are_fresh", "freshness", False, None, "age_days column must exist"),
            ]
        )

    passed_checks = sum(1 for check in checks if check["success"])
    failed_checks = len(checks) - passed_checks
    report_path = settings.paths.quality_dir / f"{safe_slug(report_name)}_quality_report.json"
    payload = {
        "report_name": report_name,
        "generated_at": datetime.now(UTC).isoformat(),
        "success": failed_checks == 0,
        "total_rows": total_rows,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "artifact_path": str(report_path),
        "checks": checks,
    }
    write_json(report_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize dataset freshness from publication dates and ``age_days``."""
    output_path = Path(report_path)
    total_rows = int(len(df))

    if "published" in df.columns:
        published = pd.to_datetime(df["published"], errors="coerce", utc=True)
    else:
        published = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")

    valid_dates = published.notna()
    missing_published_rows = int((~valid_dates).sum())
    now = pd.Timestamp.now(tz="UTC").normalize()
    derived_age_days = (now - published.dt.normalize()).dt.days

    if "age_days" in df.columns:
        recorded_age_days = pd.to_numeric(df["age_days"], errors="coerce")
        stale_mask = (recorded_age_days > settings.freshness_threshold_days) | (
            derived_age_days > settings.freshness_threshold_days
        )
        # A cleaning sentinel such as ``age_days=-1`` means an invalid or
        # missing date, not a future publication. Future status comes from
        # the source date itself.
        future_mask = derived_age_days < 0
        age_date_mismatch_rows = int(
            (
                recorded_age_days.notna()
                & derived_age_days.notna()
                & ((recorded_age_days - derived_age_days).abs() > 1)
            ).sum()
        )
    else:
        stale_mask = derived_age_days > settings.freshness_threshold_days
        future_mask = derived_age_days < 0
        age_date_mismatch_rows = 0

    stale_rows = int(stale_mask.fillna(False).sum())
    future_published_rows = int(future_mask.fillna(False).sum())

    latest = published.max() if valid_dates.any() else None
    oldest = published.min() if valid_dates.any() else None
    latest_published = latest.date().isoformat() if latest is not None else None
    oldest_published = oldest.date().isoformat() if oldest is not None else None

    is_fresh = (
        total_rows > 0
        and missing_published_rows == 0
        and stale_rows == 0
        and future_published_rows == 0
        and age_date_mismatch_rows == 0
    )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "valid_published_rows": int(valid_dates.sum()),
        "missing_published_rows": missing_published_rows,
        "future_published_rows": future_published_rows,
        "age_date_mismatch_rows": age_date_mismatch_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
        "artifact_path": str(output_path),
    }
    write_json(output_path, payload)
    return payload
