from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import read_json, write_csv, write_json


def corrupt_clean_dataframe(
    df: pd.DataFrame | None = None,
    output_log_path: Path | str | None = None,
    input_clean_path: Path | str | None = None,
    output_corrupted_path: Path | str | None = None,
) -> pd.DataFrame:
    """Gây nhiễu dữ liệu (Data Corruption Simulation):
    1. Drop một số records (drop latest papers).
    2. Chèn bản ghi duplicate (Add duplicate rows).
    3. Blank / NULL summary ở một số dòng.
    4. Chèn ký tự rác / HTML rác vào summary.
    5. Truncate title hoặc xóa title.
    6. Thay đổi ngày xuất bản thành ngày rất cũ (outdated / stale).
    7. Rebuild text_for_embedding.
    8. Ghi corruption log và lưu corrupted_papers.json.
    """
    if df is None:
        clean_path = Path(input_clean_path) if input_clean_path else Path("data/clean/cleaned_papers.json")
        if not clean_path.exists():
            clean_path = Path("data/clean/papers_clean.json")
        if not clean_path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found at {clean_path}")
        records = read_json(clean_path)
        df = pd.DataFrame(records)

    if df.empty:
        raise ValueError("Cannot corrupt an empty DataFrame.")

    corrupted_df = df.copy()
    corruption_log: list[dict[str, Any]] = []

    # 1. Drop a couple of records
    dropped_ids = corrupted_df.iloc[:2]["paper_id"].tolist()
    corrupted_df = corrupted_df.iloc[2:].reset_index(drop=True)
    corruption_log.append(
        {
            "action": "drop_records",
            "description": f"Dropped {len(dropped_ids)} latest records",
            "paper_ids": dropped_ids,
        }
    )

    # 2. Blank / NULL summary on some rows
    if len(corrupted_df) > 0:
        blank_idx = [0]
        for idx in blank_idx:
            paper_id = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "summary"] = ""
            corrupted_df.at[idx, "summary_chars"] = 0
            corruption_log.append(
                {
                    "action": "blank_summary",
                    "description": "Set summary to empty string / NULL",
                    "paper_id": paper_id,
                }
            )

    # 3. Inject noise / HTML rác into summary
    if len(corrupted_df) > 1:
        noise_idx = [1]
        for idx in noise_idx:
            paper_id = corrupted_df.at[idx, "paper_id"]
            original_summary = str(corrupted_df.at[idx, "summary"])
            junk_html = '<div class="ad_spam_junk">BUY CHEAP ITEMS NOW! CLICK HERE!!! <script>alert("junk")</script></div> '
            noisy_summary = junk_html + original_summary[:10] + " !!!GARBAGE_NOISE_DATA!!!"
            corrupted_df.at[idx, "summary"] = noisy_summary
            corrupted_df.at[idx, "summary_chars"] = len(noisy_summary)
            corruption_log.append(
                {
                    "action": "inject_noise",
                    "description": "Injected HTML junk tags and noise string into summary",
                    "paper_id": paper_id,
                }
            )

    # 4. Truncate title
    if len(corrupted_df) > 2:
        trunc_idx = [2]
        for idx in trunc_idx:
            paper_id = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "title"] = "Safe"
            corruption_log.append(
                {
                    "action": "truncate_title",
                    "description": "Truncated title to 4 characters",
                    "paper_id": paper_id,
                }
            )

    # 5. Outdated / Stale published date
    if len(corrupted_df) > 3:
        stale_idx = [3, 4]
        for idx in stale_idx:
            paper_id = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "published"] = "2020-01-01"
            corrupted_df.at[idx, "published_date"] = "2020-01-01"
            corrupted_df.at[idx, "age_days"] = 2400
            corruption_log.append(
                {
                    "action": "stale_published_date",
                    "description": "Set published date to outdated date (2020-01-01, age_days=2400)",
                    "paper_id": paper_id,
                }
            )

    # 6. Add duplicate rows (Duplicate DOI)
    if len(corrupted_df) > 5:
        dup_rows = corrupted_df.iloc[4:6].copy()
        corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
        corruption_log.append(
            {
                "action": "add_duplicates",
                "description": f"Duplicated {len(dup_rows)} existing rows to create duplicate DOIs",
                "paper_ids": dup_rows["paper_id"].tolist(),
            }
        )

    # 7. Rebuild text_for_embedding
    rebuilt_texts = []
    for _, row in corrupted_df.iterrows():
        title = str(row.get("title", ""))
        summary = str(row.get("summary", ""))
        authors_joined = str(row.get("authors_joined", ""))
        rebuilt_texts.append(f"Title: {title}\nAuthors: {authors_joined}\nSummary: {summary}")
    corrupted_df["text_for_embedding"] = rebuilt_texts

    # 8. Save log and output files
    log_target = Path(output_log_path) if output_log_path else Path("data/results/corruption_log.json")
    write_json(log_target, corruption_log)

    corrupted_json = corrupted_df.to_dict(orient="records")

    target_corrupted = Path(output_corrupted_path) if output_corrupted_path else Path("data/corrupted/corrupted_papers.json")
    write_json(target_corrupted, corrupted_json)

    alt_path1 = Path("data/corrupted/corrupted_papers.json")
    if alt_path1 != target_corrupted:
        write_json(alt_path1, corrupted_json)

    alt_path2 = Path("data/clean/papers_clean_corrupted.json")
    write_json(alt_path2, corrupted_json)

    alt_path3 = Path("data/clean/papers_clean_corrupted.csv")
    write_csv(corrupted_df, alt_path3)

    return corrupted_df

