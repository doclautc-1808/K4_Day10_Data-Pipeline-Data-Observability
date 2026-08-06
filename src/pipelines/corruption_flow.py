from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import _records_for_json, _validate_test_set
from retrieval.index import LocalEmbeddingIndex


def _require_artifacts(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        formatted = "\n- ".join(missing)
        raise RuntimeError(
            "Corruption flow requires a completed baseline. Missing artifacts:\n"
            f"- {formatted}\nRun script/run_phase1.py first."
        )


def _load_dataframe(path: Path, artifact_name: str) -> pd.DataFrame:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise RuntimeError(f"{artifact_name} must be a JSON list: {path}")
    df = pd.DataFrame(payload)
    if df.empty:
        raise RuntimeError(f"{artifact_name} is empty: {path}")
    return df


def _save_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(df, csv_path)
    write_json(json_path, _records_for_json(df))


def _ensure_separate_state_paths(settings: Settings) -> None:
    """Protect baseline artifacts from accidental corrupted/repaired overwrites."""
    groups = {
        "clean JSON": [
            settings.paths.clean_json,
            settings.paths.corrupted_clean_json,
            settings.paths.repaired_clean_json,
        ],
        "embedding manifest": [
            settings.paths.embeddings_json,
            settings.paths.corrupted_embeddings_json,
            settings.paths.repaired_embeddings_json,
        ],
        "metrics": [
            settings.paths.baseline_metrics,
            settings.paths.corrupted_metrics,
            settings.paths.repaired_metrics,
        ],
        "answers": [
            settings.paths.baseline_answers,
            settings.paths.corrupted_answers,
            settings.paths.repaired_answers,
        ],
    }
    for artifact_type, paths in groups.items():
        resolved = [path.resolve() for path in paths]
        if len(set(resolved)) != len(resolved):
            raise RuntimeError(f"Baseline/corrupted/repaired {artifact_type} paths must be distinct.")


def _validate_baseline_metrics(metrics: Any, test_set_size: int) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise RuntimeError("Baseline metrics artifact must be a JSON object.")
    required_metrics = {
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    }
    missing_metrics = sorted(required_metrics.difference(metrics))
    if missing_metrics:
        raise RuntimeError(
            f"Baseline metrics are missing required values: {', '.join(missing_metrics)}."
        )
    if int(metrics["samples"]) != test_set_size:
        raise RuntimeError(
            "Baseline metrics and frozen test set do not match: "
            f"metrics samples={metrics['samples']}, test set samples={test_set_size}."
        )
    return metrics


def main() -> None:
    """Run controlled corruption, repair from raw, and three-state comparison."""
    settings = load_settings()
    _ensure_separate_state_paths(settings)
    _require_artifacts(
        [
            settings.paths.raw_records_json,
            settings.paths.clean_json,
            settings.paths.eval_testset,
            settings.paths.baseline_metrics,
            settings.paths.baseline_answers,
            settings.paths.embeddings_json,
        ]
    )

    baseline_df = _load_dataframe(settings.paths.clean_json, "Baseline clean dataset")
    test_set = _validate_test_set(read_json(settings.paths.eval_testset), baseline_df)
    baseline_metrics = _validate_baseline_metrics(
        read_json(settings.paths.baseline_metrics), len(test_set)
    )

    corrupted_df = corrupt_clean_dataframe(
        df=baseline_df,
        output_log_path=settings.paths.corruption_log,
        output_corrupted_path=settings.paths.corrupted_clean_json,
    )
    if corrupted_df.empty:
        raise RuntimeError("Corruption produced an empty dataset; comparison cannot continue.")
    _save_dataframe(
        corrupted_df,
        settings.paths.corrupted_clean_csv,
        settings.paths.corrupted_clean_json,
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(
        corrupted_df, settings, report_name="corrupted"
    )
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, corrupted_freshness_path
    )

    raw_records = load_raw_records(settings.paths.raw_records_json)
    if not raw_records:
        raise RuntimeError("Raw snapshot is empty; repaired data cannot be rebuilt from source evidence.")
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    if repaired_df.empty:
        raise RuntimeError("Repair cleaning produced an empty dataset.")
    _save_dataframe(
        repaired_df,
        settings.paths.repaired_clean_csv,
        settings.paths.repaired_clean_json,
    )
    _validate_test_set(test_set, repaired_df)
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(
        repaired_df, settings, report_name="repaired"
    )
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(
        repaired_df, settings, repaired_freshness_path
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_evaluation.summary,
        repaired_metrics=repaired_evaluation.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print(
        "Corruption flow completed: "
        f"baseline={len(baseline_df)} rows, corrupted={len(corrupted_df)} rows, "
        f"repaired={len(repaired_df)} rows; "
        f"retrieval_hit_rate "
        f"{baseline_metrics['retrieval_hit_rate']:.4f} -> "
        f"{corrupted_evaluation.summary['retrieval_hit_rate']:.4f} -> "
        f"{repaired_evaluation.summary['retrieval_hit_rate']:.4f}."
    )
