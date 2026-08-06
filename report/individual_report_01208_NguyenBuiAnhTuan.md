# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                                                                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Họ và tên       | Nguyễn Bùi Anh Tuấn                                                                                                                                  |
| MSSV               | 2A202601208                                                                                                                                             |
| Khóa/Lớp         | K4                                                                                                                                                      |
| Tên nhóm         | My3Mien                                                                                                                                                 |
| Vai trò chính    | Thành viên 3: Observability                                                                                                                           |
| Repository         | [github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability.git](https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability.git) |
| Ngày hoàn thành | [2026-08-06]                                                                                                                                            |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data-quality validation | `src/observability/quality.py`: `run_data_quality_checks` | Clean dataframe và `Settings` | `data/quality/*_quality_report.json`, gồm 11 checks có thể audit | Hoàn thành |
| Freshness monitoring | `src/observability/quality.py`: `build_freshness_report` | `published`, `age_days`, ngưỡng 180 ngày | Freshness JSON có latest/oldest date, stale/missing/future rows và trạng thái | Hoàn thành |
| Baseline reporting | `src/observability/reporting.py`: `generate_phase1_report` | Source summary, baseline metrics, quality, freshness | `data/reports/phase1_report.md` | Hoàn thành |
| Comparison reporting | `src/observability/reporting.py`: `generate_corruption_report` | Metrics và signals corrupted/repaired | `data/reports/corruption_report.md` có delta và evidence | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Tích hợp baseline | `src/pipelines/phase1.py` | Kết nối evaluation với quality, freshness và baseline report; baseline tạo 15 samples và các artifact tương ứng. |
| Debug contract đánh giá | `src/retrieval/qa.py`, `src/evaluation/testset.py` | Phát hiện pattern câu hỏi authors/categories không khớp QA extractor; đây là nguyên nhân làm answer metric thấp khi retrieval vẫn đúng. |
| Đối chiếu artifact repair | `src/pipelines/corruption_flow.py`, `data/results/` | Phát hiện `repaired_metrics.json` đang có 120 samples trong khi baseline/corrupted có 15; không dùng metric repaired này để kết luận recovery agent. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Kiểm tra data quality | `quality.py`, `baseline_quality_report.json`, `corrupted_quality_report.json`, `repaired_quality_report.json` | Baseline/repaired: 9 pass, 2 fail; corrupted: 5 pass, 6 fail | Đọc trường `passed_checks`, `failed_checks`, `checks` trong JSON |
| Theo dõi freshness | `quality.py`, các freshness reports | Corrupted có 3 stale và 5 missing dates; repaired trở về 0 stale và 2 missing, bằng baseline | Đối chiếu `stale_rows`, `missing_published_rows`, `is_fresh` |
| Sinh báo cáo evidence | `reporting.py`, `phase1_report.md`, `corruption_report.md` | Báo cáo hiển thị metric, quality/freshness và delta corruption/repair | Mở Markdown và đối chiếu với JSON trong `data/results/` và `data/quality/` |

Output trọng tâm của phần việc là `data/reports/corruption_report.md`: report cho thấy corruption làm cả bốn metric chính giảm, đồng thời quality giảm từ 9 pass/2 fail xuống 5 pass/6 fail. Đây là bằng chứng để liên hệ data quality với chất lượng RAG thay vì chỉ báo rằng script đã chạy.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần phát hiện dữ liệu không đáng tin trước khi user nhận câu trả lời sai. Vì vậy phần observability phải vừa kiểm tra contract của clean dataframe, vừa theo dõi freshness, rồi ghi kết quả dưới dạng artifact có thể đối chiếu với metrics và báo cáo.

### Cách triển khai

`run_data_quality_checks` kiểm tra row count, schema bắt buộc, `paper_id` null/unique theo dạng không phân biệt hoa thường, title/summary/text embedding rỗng, summary tối thiểu 50 ký tự, ngày xuất bản hợp lệ và `age_days`. Mỗi check trả về tên, quality dimension, observed value, expectation và trạng thái; nhờ đó report không cần hard-code PASS/FAIL.

`build_freshness_report` parse cột `published`, tổng hợp ngày mới nhất/cũ nhất, stale rows, missing dates, future dates và độ lệch giữa `published` với `age_days`. Giá trị `age_days=-1` được hiểu là date thiếu/không hợp lệ, không bị báo sai là future date.

Hai hàm reporting nhận JSON kết quả thực tế, render bảng Markdown và tính delta `corrupted - baseline`, `repaired - corrupted`. Báo cáo chỉ nêu recovery khi metric/signal được cung cấp cho thấy có cải thiện.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Clean dataframe có `paper_id`, `title`, `summary`, `published`, `age_days`, `text_for_embedding`; `Settings.freshness_threshold_days=180` |
| Output | Quality payload có `success`, `passed_checks`, `failed_checks`, `checks`; freshness payload có `stale_rows`, `missing_published_rows`, `is_fresh`; hai Markdown reports |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py`, `pandas` |
| Module sử dụng output | `phase1.py`, `corruption_flow.py`, nhóm viết báo cáo và người chấm |
| Điều kiện lỗi cần xử lý | Missing schema, blank/null fields, DOI trùng, summary ngắn, date không parse được, `age_days` âm, stale/future data |

### Cách xác minh

```powershell
.\.venv\Scripts\python.exe script\run_phase1.py
.\.venv\Scripts\python.exe script\run_corruption_flow.py
```

- **Kết quả mong đợi:** tạo metrics, answers, quality/freshness JSON và Markdown reports; corruption phải làm signals xấu đi, repair phải được đối chiếu với baseline.
- **Kết quả thực tế:** baseline có 24 clean records, 15 evaluation samples; corruption có 15 samples và giảm `retrieval_hit_rate` từ 1.0000 xuống 0.6000. Quality/freshness của repaired trở lại đúng mức baseline.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/quality/`, `data/reports/` và `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cách biểu diễn quality result để pipeline, report và người chấm cùng đọc được; đồng thời pipeline không được dừng ngay khi gặp schema/data lỗi vì khi đó mất bằng chứng observability.
- **Các phương án đã cân nhắc:** (1) raise exception ở check đầu tiên; (2) chỉ in warning ra terminal; (3) ghi payload có cấu trúc cho toàn bộ checks.
- **Phương án đã chọn:** Mỗi check trả về JSON gồm status, observed value và expectation; pipeline vẫn hoàn tất để sinh report evidence.
- **Lý do:** Cách này giữ được toàn bộ dấu vết lỗi, hỗ trợ so sánh baseline/corrupted/repaired và không biến một lỗi data thành lỗi không thể chẩn đoán.
- **Bằng chứng quyết định phù hợp:** Corrupted report chỉ ra đồng thời 4 DOI thuộc nhóm duplicate, 1 blank/short summary, 5 invalid publication dates và 3 stale rows; repaired report xác nhận những lỗi do corruption đã quay về mức baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Freshness có thể hiểu `age_days=-1` là future publication, trong khi `-1` là sentinel từ cleaning cho date thiếu/không parse được.
- **Lệnh hoặc bước tái hiện:** Chạy baseline và kiểm tra `data/quality/freshness_report.json`.
- **Nguyên nhân gốc:** Logic freshness dùng giá trị age âm để suy luận future date thay vì suy luận từ chính `published` đã parse.
- **Cách xử lý:** Future status được tính từ publication date; row có `age_days=-1` được ghi nhận riêng trong `missing_published_rows` và `age_days_valid`.
- **Cách xác minh sau khi sửa:** Freshness artifact hiện có `future_published_rows=0`, `missing_published_rows=2`; quality chỉ rõ 2 lỗi date thay vì gộp sai vào future.
- **Điều học được:** Sentinel kỹ thuật không phải business fact; observability phải phân biệt rõ missing, invalid, stale và future để root cause không bị sai lệch.

Blocker còn lại:

- **Phạm vi bị ảnh hưởng:** `published_date_valid`, `age_days_valid` của baseline/repaired và khả năng so sánh metric repaired.
- **Những gì đã loại trừ:** Không có duplicate DOI, title rỗng, summary rỗng hay stale row ở baseline/repaired; cả hai trạng thái đều có đúng 24 rows.
- **Bước tiếp theo:** Sửa extraction/fallback publication date ở ingestion hoặc loại record date không hợp lệ theo contract cleaning; chạy lại repaired evaluation với đúng frozen `data/eval/test_set.json` để `samples=15` giống baseline/corrupted.

## 7. Hiểu biết về luồng end-to-end

1. Crossref API trả response JSON; ingestion lưu raw response và raw records. Cleaning chuẩn hóa field, tính `age_days`, tạo `text_for_embedding`, sau đó `LocalEmbeddingIndex` embed các documents bằng MiniLM và lưu collection ChromaDB.
2. Test set lưu question, ground truth và `ground_truth_doc_ids`. Khi evaluate, retrieval hit là đúng nếu ground-truth ID xuất hiện trong top-k; answer được so với ground truth bằng Token F1 và judge score.
3. Quality checks đo completeness, uniqueness, validity và schema ở từng record. Freshness monitoring tập trung vào thời gian: khoảng ngày publish, stale/missing/future dates và tính nhất quán với `age_days`.
4. Phải giữ nguyên test set để chênh lệch metric chỉ phản ánh thay đổi dữ liệu/index do corruption hoặc repair, không bị nhiễu bởi câu hỏi khác.
5. Repair chỉ được xem là thành công khi rebuilt từ raw source, corruption-specific quality/freshness signals quay về baseline và metrics được chạy lại trên cùng test set. Nếu sample count khác nhau, không được kết luận metric đã phục hồi.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 0.7500* | Corruption làm mất 6/15 retrieval hits; metric repaired chưa so sánh được vì sample count khác. |
| `mean_token_f1` | 0.7516 | 0.4179 | 0.0956* | Blank/noisy summary và title truncation làm answer overlap giảm; repaired metric hiện không cùng evaluation set. |
| `judge_accuracy` | 0.6667 | 0.4000 | 0.0000* | Corruption làm tỷ lệ đúng giảm; cần re-evaluate repaired trên 15 questions. |
| `mean_judge_score` | 3.6667 | 2.6000 | 1.0000* | Điểm judge giảm sau corruption; chưa dùng repaired value để kết luận recovery. |
| Quality checks | FAIL — 9 pass/2 fail | FAIL — 5 pass/6 fail | FAIL — 9 pass/2 fail | Damage do corruption được phục hồi; 2 lỗi publication date có sẵn từ baseline còn lại. |
| Freshness status | FAIL — 0 stale, 2 missing | FAIL — 3 stale, 5 missing | FAIL — 0 stale, 2 missing | Repair đưa freshness signal trở về baseline, dù baseline vốn chưa fresh hoàn toàn. |

\* `repaired_metrics.json` hiện có `samples=120`, trong khi baseline/corrupted đều có `samples=15`. Các giá trị repaired không cùng điều kiện đánh giá nên chỉ được ghi nhận là artifact hiện tại, không được dùng để kết luận mức phục hồi chất lượng agent.

### Kết luận từ số liệu

1. Drop 2 latest papers có trong frozen test set → `paper_id` không còn trong index cho 6 câu hỏi → `retrieval_hit_rate` giảm từ 1.0000 xuống 0.6000. Đồng thời blank summary, duplicate DOI và stale dates làm corrupted quality giảm từ 9 pass/2 fail xuống 5 pass/6 fail.
2. Rebuild repaired dataset từ raw records → uniqueness, blank-summary và freshness damage do corruption quay về baseline (9 pass/2 fail; 0 stale, 2 missing). Tuy nhiên agent metric recovery chưa thể kết luận với artifact hiện tại vì repaired evaluation có 120 samples, không phải 15.

Corruption ảnh hưởng rõ nhất tới retrieval là `drop_records`: hai paper bị bỏ đều có câu hỏi trong test set, nên tác động trực tiếp tới document IDs cần tìm. Những corruption khác chủ yếu làm giảm answer quality và quality/freshness signals.

Kết quả khác kỳ vọng là repaired quality/freshness vẫn FAIL và repaired metrics lại dùng 120 samples. Kiểm tra JSON cho thấy repair đã đưa data signals trở về baseline; FAIL còn lại đến từ hai publication date không hợp lệ vốn tồn tại ở raw baseline. Cần đồng bộ lại corruption flow để repaired dùng đúng frozen test set trước khi so sánh metric.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Artifact raw/clean/index/metrics phải tách riêng để truy được nguyên nhân khi metric thay đổi; chỉ log terminal là không đủ.
2. Một trạng thái overall FAIL cần được phân rã theo check: repaired vẫn FAIL không có nghĩa repair thất bại nếu corruption-specific signals đã quay về baseline.
3. Evaluation chỉ công bằng khi frozen test set, ground-truth IDs, top-k và sample count giống nhau ở cả ba trạng thái.

### Nếu có thêm thời gian

Tôi sẽ bổ sung data contract cho publication date ngay ở ingestion/cleaning: fallback theo nhiều Crossref date fields, log row bị loại và test cho date thiếu. Sau đó chạy lại toàn bộ baseline/corrupted/repaired với cùng 15 questions; tiêu chí đo là quality/freshness baseline PASS và mọi metric repaired được phép so sánh trực tiếp với baseline.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Nguyễn Bùi Anh Tuấn]
**Ngày xác nhận:** [2026-08-06]
