# Corruption and Recovery Comparison Report

## Metric comparison

| Metric | Baseline | Corrupted | Repaired | Corruption delta | Repair delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `samples` | 15 | 15 | 15 | +0.0000 | +0.0000 |
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | -0.4000 | +0.4000 |
| `mean_token_f1` | 0.7516 | 0.4179 | 0.7516 | -0.3337 | +0.3337 |
| `judge_accuracy` | 0.6667 | 0.4000 | 0.6667 | -0.2667 | +0.2667 |
| `mean_judge_score` | 3.6667 | 2.6000 | 3.6667 | -1.0667 | +1.0667 |

Corruption delta = corrupted − baseline. Repair delta = repaired − corrupted.

## Quality and freshness signals

| Signal | Corrupted | Repaired |
| --- | ---: | ---: |
| Quality status | FAIL | FAIL |
| Passed quality checks | 5 | 9 |
| Failed quality checks | 6 | 2 |
| Freshness status | FAIL | FAIL |
| Stale rows | 3 | 0 |
| Missing publication dates | 5 | 2 |
| Age/date mismatches | 0 | 0 |

## Observed outcome

- Metrics lower after corruption: `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`.
- Metrics higher after repair: `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`.
- Quality changed from **FAIL** to **FAIL**.
- Freshness changed from **FAIL** to **FAIL**.

These statements describe the supplied measurements only; they do not claim recovery when no improvement is present.

## Evidence

- Corrupted quality artifact: `/Users/binhtran23/Documents/Vin_uni/K4_Day10_Data-Pipeline-Data-Observability/data/quality/corrupted_quality_report.json`
- Repaired quality artifact: `/Users/binhtran23/Documents/Vin_uni/K4_Day10_Data-Pipeline-Data-Observability/data/quality/repaired_quality_report.json`
- Corrupted freshness artifact: `/Users/binhtran23/Documents/Vin_uni/K4_Day10_Data-Pipeline-Data-Observability/data/quality/corrupted_freshness_report.json`
- Repaired freshness artifact: `/Users/binhtran23/Documents/Vin_uni/K4_Day10_Data-Pipeline-Data-Observability/data/quality/repaired_freshness_report.json`
