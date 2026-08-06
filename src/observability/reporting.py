from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.utils import write_text


CORE_METRICS = (
    "samples",
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)


def _escape_markdown(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _delta(current: Any, previous: Any) -> str:
    current_number = _number(current)
    previous_number = _number(previous)
    if current_number is None or previous_number is None:
        return "N/A"
    return f"{current_number - previous_number:+.4f}"


def _quality_status(quality: dict[str, Any]) -> str:
    return "PASS" if quality.get("success", False) else "FAIL"


def _quality_check_rows(quality: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for check in quality.get("checks", []):
        rows.append(
            "| {name} | {dimension} | {status} | {observed} | {expectation} |".format(
                name=_escape_markdown(check.get("name")),
                dimension=_escape_markdown(check.get("dimension")),
                status="PASS" if check.get("success", False) else "FAIL",
                observed=_escape_markdown(check.get("observed_value")),
                expectation=_escape_markdown(check.get("expectation")),
            )
        )
    if not rows:
        rows.append("| N/A | N/A | N/A | N/A | No quality checks were supplied. |")
    return rows


def _source_rows(source_summary: dict[str, Any]) -> list[str]:
    if not source_summary:
        return ["| N/A | No source summary was supplied. |"]
    return [
        f"| {_escape_markdown(key)} | {_escape_markdown(value)} |"
        for key, value in source_summary.items()
    ]


def _ragas_summary(metrics: dict[str, Any]) -> str:
    ragas = metrics.get("ragas")
    if not ragas:
        return "N/A"
    if isinstance(ragas, dict) and "skipped" in ragas:
        return f"Skipped: {_escape_markdown(ragas['skipped'])}"
    if isinstance(ragas, dict) and "error" in ragas:
        return f"Error: {_escape_markdown(ragas['error'])}"
    return _escape_markdown(ragas)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate the baseline report directly from pipeline artifacts."""
    metric_rows = [
        f"| `{name}` | {_escape_markdown(metrics.get(name))} |" for name in CORE_METRICS
    ]
    quality_rows = _quality_check_rows(quality)
    lines = [
        "# Phase 1 — Baseline Data Pipeline Report",
        "",
        "## Overall status",
        "",
        f"- Data quality: **{_quality_status(quality)}**",
        f"- Freshness: **{'PASS' if freshness.get('is_fresh', False) else 'FAIL'}**",
        f"- Evaluated samples: **{_escape_markdown(metrics.get('samples'))}**",
        "",
        "## Source and pipeline summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        *_source_rows(source_summary),
        "",
        "## Evaluation metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        *metric_rows,
        "",
        f"Ragas: {_ragas_summary(metrics)}",
        "",
        "## Data quality checks",
        "",
        f"Passed checks: **{_escape_markdown(quality.get('passed_checks'))}**  ",
        f"Failed checks: **{_escape_markdown(quality.get('failed_checks'))}**",
        "",
        "| Check | Dimension | Status | Observed | Expectation |",
        "| --- | --- | --- | ---: | --- |",
        *quality_rows,
        "",
        "## Freshness",
        "",
        "| Signal | Value |",
        "| --- | ---: |",
        f"| Latest publication | {_escape_markdown(freshness.get('latest_published'))} |",
        f"| Oldest publication | {_escape_markdown(freshness.get('oldest_published'))} |",
        f"| Total rows | {_escape_markdown(freshness.get('total_rows'))} |",
        f"| Stale rows | {_escape_markdown(freshness.get('stale_rows'))} |",
        f"| Missing publication dates | {_escape_markdown(freshness.get('missing_published_rows'))} |",
        f"| Future publication dates | {_escape_markdown(freshness.get('future_published_rows'))} |",
        f"| Age/date mismatches | {_escape_markdown(freshness.get('age_date_mismatch_rows'))} |",
        f"| Threshold (days) | {_escape_markdown(freshness.get('freshness_threshold_days'))} |",
        f"| Freshness status | {'PASS' if freshness.get('is_fresh', False) else 'FAIL'} |",
        "",
        "## Evidence",
        "",
        f"- Quality artifact: `{_escape_markdown(quality.get('artifact_path'))}`",
        f"- Freshness artifact: `{_escape_markdown(freshness.get('artifact_path'))}`",
        "",
        "This report is generated from the supplied artifacts; a PASS is not hard-coded.",
    ]
    write_text(Path(report_path), "\n".join(lines) + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Generate an evidence-based baseline/corrupted/repaired comparison."""
    comparison_rows: list[str] = []
    for name in CORE_METRICS:
        baseline = baseline_metrics.get(name)
        corrupted = corrupted_metrics.get(name)
        repaired = repaired_metrics.get(name)
        comparison_rows.append(
            f"| `{name}` | {_escape_markdown(baseline)} | {_escape_markdown(corrupted)} | "
            f"{_escape_markdown(repaired)} | {_delta(corrupted, baseline)} | {_delta(repaired, corrupted)} |"
        )

    corrupted_quality_status = _quality_status(corrupted_quality)
    repaired_quality_status = _quality_status(repaired_quality)
    corrupted_freshness_status = "PASS" if corrupted_freshness.get("is_fresh", False) else "FAIL"
    repaired_freshness_status = "PASS" if repaired_freshness.get("is_fresh", False) else "FAIL"

    recovered_metrics: list[str] = []
    degraded_metrics: list[str] = []
    for name in CORE_METRICS[1:]:
        baseline = _number(baseline_metrics.get(name))
        corrupted = _number(corrupted_metrics.get(name))
        repaired = _number(repaired_metrics.get(name))
        if baseline is None or corrupted is None or repaired is None:
            continue
        if corrupted < baseline:
            degraded_metrics.append(name)
        if repaired > corrupted:
            recovered_metrics.append(name)

    degradation_text = ", ".join(f"`{name}`" for name in degraded_metrics) or "none observed"
    recovery_text = ", ".join(f"`{name}`" for name in recovered_metrics) or "none observed"

    lines = [
        "# Corruption and Recovery Comparison Report",
        "",
        "## Metric comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Corruption delta | Repair delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *comparison_rows,
        "",
        "Corruption delta = corrupted − baseline. Repair delta = repaired − corrupted.",
        "",
        "## Quality and freshness signals",
        "",
        "| Signal | Corrupted | Repaired |",
        "| --- | ---: | ---: |",
        f"| Quality status | {corrupted_quality_status} | {repaired_quality_status} |",
        f"| Passed quality checks | {_escape_markdown(corrupted_quality.get('passed_checks'))} | {_escape_markdown(repaired_quality.get('passed_checks'))} |",
        f"| Failed quality checks | {_escape_markdown(corrupted_quality.get('failed_checks'))} | {_escape_markdown(repaired_quality.get('failed_checks'))} |",
        f"| Freshness status | {corrupted_freshness_status} | {repaired_freshness_status} |",
        f"| Stale rows | {_escape_markdown(corrupted_freshness.get('stale_rows'))} | {_escape_markdown(repaired_freshness.get('stale_rows'))} |",
        f"| Missing publication dates | {_escape_markdown(corrupted_freshness.get('missing_published_rows'))} | {_escape_markdown(repaired_freshness.get('missing_published_rows'))} |",
        f"| Age/date mismatches | {_escape_markdown(corrupted_freshness.get('age_date_mismatch_rows'))} | {_escape_markdown(repaired_freshness.get('age_date_mismatch_rows'))} |",
        "",
        "## Observed outcome",
        "",
        f"- Metrics lower after corruption: {degradation_text}.",
        f"- Metrics higher after repair: {recovery_text}.",
        f"- Quality changed from **{corrupted_quality_status}** to **{repaired_quality_status}**.",
        f"- Freshness changed from **{corrupted_freshness_status}** to **{repaired_freshness_status}**.",
        "",
        "These statements describe the supplied measurements only; they do not claim recovery when no improvement is present.",
        "",
        "## Evidence",
        "",
        f"- Corrupted quality artifact: `{_escape_markdown(corrupted_quality.get('artifact_path'))}`",
        f"- Repaired quality artifact: `{_escape_markdown(repaired_quality.get('artifact_path'))}`",
        f"- Corrupted freshness artifact: `{_escape_markdown(corrupted_freshness.get('artifact_path'))}`",
        f"- Repaired freshness artifact: `{_escape_markdown(repaired_freshness.get('artifact_path'))}`",
    ]
    write_text(Path(report_path), "\n".join(lines) + "\n")
