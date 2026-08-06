from __future__ import annotations

import json
import uuid
from typing import Any
from pathlib import Path

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) == 0:
        return []
        
    test_set = []
    
    # Kiem tra so luong document toi thieu va chon paper dai dien
    sample_df = df.head(min(5, len(df)))
    
    for _, row in sample_df.iterrows():
        paper_id = row.get("paper_id", "")
        title = row.get("title", "")
        summary = row.get("summary", "")
        authors = row.get("authors_joined", "")
        published = row.get("published", "")
        categories = row.get("categories_joined", "")
        
        # summary
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "summary",
            "question": f"What is the summary of the paper titled '{title}'?",
            "ground_truth": summary,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # authors
        if authors:
            test_set.append({
                "id": str(uuid.uuid4()),
                "question_type": "authors",
                "question": f"Who are the authors of the paper '{title}'?",
                "ground_truth": authors,
                "ground_truth_doc_ids": [paper_id]
            })
            
        # date
        if published:
            test_set.append({
                "id": str(uuid.uuid4()),
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": str(published),
                "ground_truth_doc_ids": [paper_id]
            })
            
        # categories
        if categories:
            test_set.append({
                "id": str(uuid.uuid4()),
                "question_type": "categories",
                "question": f"What are the categories for the paper '{title}'?",
                "ground_truth": categories,
                "ground_truth_doc_ids": [paper_id]
            })
            
    # Ghi file JSON vao output_path
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)
        
    return test_set
