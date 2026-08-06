from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _load_or_fetch_records(settings: Settings):
    """Load the frozen raw snapshot unless the caller explicitly refreshes it."""
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        return load_raw_records(settings.paths.raw_records_json), "cached raw snapshot"
    return fetch_source_records(settings), "fresh Crossref API response"


def _validate_test_set(test_set: Any, clean_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Fail early when a frozen test set no longer matches the clean corpus."""
    if not isinstance(test_set, list) or not test_set:
        raise RuntimeError("Evaluation test set is empty or is not a JSON list.")

    required_fields = {
        "id",
        "question_type",
        "question",
        "ground_truth",
        "ground_truth_doc_ids",
    }
    clean_ids = set(clean_df["paper_id"].astype(str))
    seen_sample_ids: set[str] = set()
    for position, item in enumerate(test_set):
        if not isinstance(item, dict):
            raise RuntimeError(f"Evaluation sample {position} is not a JSON object.")
        missing_fields = sorted(required_fields.difference(item))
        if missing_fields:
            raise RuntimeError(
                f"Evaluation sample {position} is missing fields: {', '.join(missing_fields)}."
            )
        sample_id = str(item["id"])
        if sample_id in seen_sample_ids:
            raise RuntimeError(f"Evaluation test set contains duplicate sample id: {sample_id}")
        seen_sample_ids.add(sample_id)

        ground_truth_ids = item["ground_truth_doc_ids"]
        if not isinstance(ground_truth_ids, list) or not ground_truth_ids:
            raise RuntimeError(
                f"Evaluation sample {sample_id} must contain at least one ground-truth document ID."
            )
        missing_doc_ids = sorted(set(map(str, ground_truth_ids)).difference(clean_ids))
        if missing_doc_ids:
            raise RuntimeError(
                f"Evaluation sample {sample_id} references IDs absent from clean data: "
                f"{', '.join(missing_doc_ids)}."
            )
    return test_set


def _load_or_build_test_set(
    clean_df: pd.DataFrame, settings: Settings
) -> tuple[list[dict[str, Any]], str]:
    """Keep the evaluation set fixed across baseline/corruption/repaired runs."""
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(settings.paths.eval_testset)
        return _validate_test_set(test_set, clean_df), "cached frozen test set"
    test_set = build_test_set(clean_df, settings.paths.eval_testset)
    return _validate_test_set(test_set, clean_df), "newly generated test set"


def _records_for_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert pandas missing values to JSON null before writing artifacts."""
    serializable = df.astype(object).where(df.notna(), None)
    return serializable.to_dict(orient="records")


def main() -> None:
    """Run the baseline flow from raw Crossref records to evidence artifacts."""
    settings = load_settings()

    records, source_mode = _load_or_fetch_records(settings)
    if not records:
        raise RuntimeError("No raw Crossref records are available for the baseline pipeline.")

    clean_df = build_clean_dataframe(records, run_date=now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced no records; cannot build an embedding index.")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, _records_for_json(clean_df))

    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    test_set, test_set_mode = _load_or_build_test_set(clean_df, settings)

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(clean_df, settings, report_name="baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    source_summary = {
        "source": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_record_count": len(records),
        "clean_record_count": len(clean_df),
        "source_mode": source_mode,
        "test_set_mode": test_set_mode,
        "test_set_samples": len(test_set),
        "embedding_model": settings.embedding_model,
        "collection_name": index.collection_name,
        "top_k": settings.top_k,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    print(
        "Baseline pipeline completed: "
        f"{len(clean_df)} clean records, {len(test_set)} evaluation samples, "
        f"retrieval_hit_rate={evaluation.summary['retrieval_hit_rate']:.4f}."
    )
