# Phase 1 — Baseline Data Pipeline Report

## Overall status

- Data quality: **FAIL**
- Freshness: **FAIL**
- Evaluated samples: **15**

## Source and pipeline summary

| Field | Value |
| --- | --- |
| source | Crossref REST API |
| source_query | agentic retrieval augmented generation large language model |
| source_filter | from-pub-date:2026-02-07,has-abstract:true |
| raw_record_count | 24 |
| clean_record_count | 24 |
| source_mode | cached raw snapshot |
| test_set_mode | cached frozen test set |
| test_set_samples | 15 |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 |
| collection_name | papers-baseline |
| top_k | 4 |

## Evaluation metrics

| Metric | Value |
| --- | ---: |
| `samples` | 15 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 0.7516 |
| `judge_accuracy` | 0.6667 |
| `mean_judge_score` | 3.6667 |

Ragas: Skipped: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## Data quality checks

Passed checks: **9**  
Failed checks: **2**

| Check | Dimension | Status | Observed | Expectation |
| --- | --- | --- | ---: | --- |
| row_count_positive | volume | PASS | 24 | row count must be greater than 0 |
| required_columns_present | schema | PASS | [] | all required columns must exist: paper_id, title, summary, published, age_days, text_for_embedding |
| paper_id_not_null | completeness | PASS | 0 | missing or blank paper_id count must equal 0 |
| paper_id_unique | uniqueness | PASS | 0 | rows participating in duplicate paper_id groups must equal 0 |
| title_not_empty | completeness | PASS | 0 | missing or blank title count must equal 0 |
| summary_not_empty | completeness | PASS | 0 | missing or blank summary count must equal 0 |
| text_for_embedding_not_empty | completeness | PASS | 0 | missing or blank text_for_embedding count must equal 0 |
| summary_min_length | validity | PASS | 0 | every summary must contain at least 50 characters |
| published_date_valid | validity | FAIL | 2 | unparseable or missing published date count must equal 0 |
| age_days_valid | validity | FAIL | 2 | age_days must be a non-negative number for every row |
| records_are_fresh | freshness | PASS | 0 | no row may exceed 180 days |

## Freshness

| Signal | Value |
| --- | ---: |
| Latest publication | 2026-08-01 |
| Oldest publication | 2026-02-12 |
| Total rows | 24 |
| Stale rows | 0 |
| Missing publication dates | 2 |
| Future publication dates | 0 |
| Age/date mismatches | 0 |
| Threshold (days) | 180 |
| Freshness status | FAIL |

## Evidence

- Quality artifact: `D:\AITHUCCHIEN\K4_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_quality_report.json`
- Freshness artifact: `D:\AITHUCCHIEN\K4_Day10_Data-Pipeline-Data-Observability\data\quality\freshness_report.json`

This report is generated from the supplied artifacts; a PASS is not hard-coded.
