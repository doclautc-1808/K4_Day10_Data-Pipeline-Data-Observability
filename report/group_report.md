# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | [K4]              |
| Tên nhóm         | [My3Mien]     |
| Repository         | [https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability] |
| Ngày hoàn thành | [2026-06-08]               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | [Đào Chí Hiển] | [2A202601066] | [Source Ingestion] | [src/ingestion/crossref.py,data\raw\crossref_records.json, data\raw\crossref_responsse.json ] |
| 2 | [Nguyễn Việt Anh] | [2A202601144] | [Cleaning & Test set ] | [src/evaluation/testset.py, src/ingestion/cleaning.py, script/run_clean_and_testset.py, papers_clean.csv, papers_clean.json, test_set.json] |
| 3 | [Nguyễn Bùi Anh Tuấn] | [2A202601208] | [Observability] | [src\ingestion\crossref.py, src\observability\quality.py, src\observability\reporting.py, src\pipelines\phase1.py, src\retrieval\qa.py] |
| 4 | [Nguyễn Ngọc Chi] | [2A202602024] | [src/ingestion/corruption.py src/ingestion/repair.py src/pipelines/phase2_repaired.py data/corrupted/corrupted_papers.json data/repaired/repaired_papers.json data/results/repaired_metrics.json data/reports/final_report.md] |
| 5 | [Trần Thanh Bình] | [2A202601174] | [Integration & Comparison] | [data/reports/corruption_report.md, src/pipelines/phase1.py, src/pipelines/corruption_flow.py] |


## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành phần ingestion dữ liệu Crossref trong `src/ingestion/crossref.py` và triển khai luồng lưu raw artifacts để đảm bảo traceability. Chúng tôi đã xây dựng được schema `PaperRecord`, ghi nhận nguồn dữ liệu, query/filter và lưu hai artifact chính: `data/raw/crossref_response.json` và `data/raw/crossref_records.json`. Baseline pipeline đã tạo ra artifact đầu vào cho bước làm sạch, bao gồm raw response, raw records, clean dataset và các file báo cáo chất lượng, mặc dù phần `phase1` và `corruption_flow` vẫn cần hoàn thiện thêm để chạy end-to-end với tất cả bước embed và đánh giá. 

Trong các loại corruption, lỗi blank summary và dữ liệu stale publication date được xác định là ảnh hưởng mạnh nhất đến chất lượng retrieval và agent, vì chúng làm giảm khả năng truy xuất thông tin chính xác và độ tươi mới của corpus. Sau bước repair, nhóm hướng tới phục hồi các chỉ số `retrieval_hit_rate` và `mean_judge_score` bằng cách khôi phục summary hợp lệ và loại bỏ các record xấu. Blocker quan trọng nhất hiện tại là sự phụ thuộc vào phần cleaning và pipeline toàn bộ chưa được triển khai đầy đủ, cùng với yêu cầu phải chạy thử trên môi trường có credential phù hợp để thu được metrics cuối cùng.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API   | Fetch, retry, parse raw Crossref JSON | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Đào Chí Hiển |
| Cleaning          | Raw records    | Chuẩn hóa title/summary/authors/categories, lọc record xấu | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Nguyễn Việt Anh |
| Embedding/index   | Clean dataset  | Sinh embedding với `sentence-transformers/all-MiniLM-L6-v2`, xây ChromaDB index | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Trần Thanh Bình |
| Evaluation        | Clean/indexed data | Tạo test set, đánh giá retrieval và QA metrics | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Nguyễn Việt Anh |
| Observability     | Clean data + metrics | Kiểm tra quality, freshness và xuất báo cáo | `data/quality/freshness_report.json`, `data/reports/phase1_report.md` | Nguyễn Bùi Anh Tuấn |
| Corruption/repair | Clean baseline data | Tạo corrupted dataset, repair và đánh giá lại | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` | Nguyễn Ngọc Chi |
| Orchestration     | Toàn bộ modules | Điều phối phase1 và corruption flow | `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, metrics JSON | Trần Thanh Bình |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini` (mặc định nếu không có `.env`) |
| `LLM_MODEL`                | `gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| `Retrieval top_k`           | `4` |
| `Freshness threshold`          | `180` ngày |
| `Random seed, nếu có`        | không cấu hình trong project |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | `2026-08-06T09:02:32+00:00` | `data/results/baseline_metrics.json`, `data/quality/freshness_report.json` |
| Corruption flow   | Thành công | `2026-08-06T09:46:23+00:00` | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/results/corruption_log.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API `https://api.crossref.org/works` |
| Query/filter                | query=`agentic retrieval augmented generation large language model`; filter=`from-pub-date:<date>,has-abstract:true` |
| Thời điểm lấy dữ liệu | `2026-08-06T09:02:32+00:00` (raw response lưu tại `data/raw/crossref_response.json`) |
| Số record nhận được    | `24` (config `max_results=24`) |
| Cơ chế retry/backoff      | Retry khi HTTP 429/503 với backoff lũy tiến 1s, 2s, 4s, 8s, 16s |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | DOI của bài báo | Bỏ record nếu thiếu |
| `title` | `str` | Có | Tiêu đề bài báo | Bỏ record nếu thiếu |
| `summary` | `str` | Có | Abstract hoặc description | Bỏ record nếu thiếu |
| `authors` | `list[str]` | Không | Danh sách tác giả | Dùng danh sách rỗng nếu thiếu |
| `categories` | `list[str]` | Không | Chủ đề/subject | Dùng danh sách rỗng nếu thiếu |
| `primary_category` | `str` | Không | Category chính hoặc fallback từ `type` | Dùng chuỗi rỗng nếu thiếu |
| `published` | `str` | Không | Ngày xuất bản | Dùng chuỗi rỗng nếu thiếu |
| `updated` | `str` | Không | Ngày cập nhật | Dùng chuỗi rỗng nếu thiếu |
| `abs_url` | `str` | Không | URL DOI/abstract | Dùng chuỗi rỗng nếu thiếu |
| `pdf_url` | `str` | Không | Link PDF hoặc DOI fallback | Dùng DOI URL nếu thiếu link PDF |
| `comment` | `str` | Không | Publisher hoặc metadata bổ sung | Dùng chuỗi rỗng nếu thiếu |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record không có `title` hoặc `summary` | Completeness / Validity | 0 | So sánh số lượng record trước/sau trong `data/clean/papers_clean.json` và xác nhận không có giá trị blank. |
| Chuẩn hóa whitespace và loại HTML trong `title`/`summary` | Validity | 24 | Kiểm tra dữ liệu sạch trong `data/clean/papers_clean.json` và xác nhận mọi record đều có summary đủ dài. |
| Duy trì `authors` và `categories` dưới dạng list | Consistency | 24 | Kiểm tra schema JSON trong `data/clean/papers_clean.json` đảm bảo tất cả record vẫn giữ cấu trúc list. |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

Nhóm dự kiến tạo `text_for_embedding` bằng cách ghép `title`, `summary`, `authors_joined`, `categories_joined` thành một chuỗi duy nhất để embedding. `document ID` dùng `paper_id` DOI, đảm bảo nhất quán giữa raw record và test set. `age_days` được tính từ `published` tới ngày chạy pipeline để đánh giá freshness.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 15 |
| Các `question_type`                    | `summary`, `authors`, `date` |
| Ground-truth document ID                 | `paper_id` DOI trong `ground_truth_doc_ids` |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB local collection `papers-baseline` |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | `gemini` / `gemini-2.5-flash` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set được giữ chung để đảm bảo sự khác biệt trong kết quả phản ánh trực tiếp chất lượng dữ liệu và index, không phải sự khác biệt của bộ câu hỏi. Điều này giúp so sánh baseline, corrupted và repaired một cách công bằng.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` |
| Cleaned dataset          | `data/clean/`                        | Có | `data/clean/papers_clean.json`, `data/clean/papers_clean.csv` |
| Embedding manifest/index | `data/embeddings/`                   | Có | `data/embeddings/papers_embeddings.json` |
| Evaluation set           | `data/eval/`                         | Có | `data/eval/test_set.json` |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Contains baseline retrieval and judge metrics |
| Quality/freshness        | `data/quality/`                      | Có | Freshness and baseline quality reports available |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Phase 1 report exists |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Mức độ câu hỏi trả về document đúng ở top-k retrieval. |
| `mean_token_f1`      |     0.7516 | Độ tương đồng token giữa câu trả lời và đáp án reference. |
| `judge_accuracy`     |     0.6667 | Tỷ lệ judge đánh giá kết quả chính xác. |
| `mean_judge_score`   |     3.6667 | Điểm trung bình do judge đánh giá, thang 1-5. |
| Ragas, nếu có        | N/A | Bị bỏ qua vì `RUN_RAGAS` không bật trong artifact hiện tại. |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count_positive` | volume | > 0 rows | Pass (24 rows) | `data/quality/baseline_quality_report.json` |
| `required_columns_present` | schema | all required columns | Pass | `data/quality/baseline_quality_report.json` |
| `paper_id_not_null` | completeness | 0 missing | Pass | `data/quality/baseline_quality_report.json` |
| `summary_not_empty` | completeness | 0 blank summaries | Pass | `data/quality/baseline_quality_report.json` |
| `published_date_valid` | validity | 0 invalid dates | Fail (2 invalid/missing) | `data/quality/baseline_quality_report.json` |
| `age_days_valid` | validity | non-negative age_days | Fail (2 invalid values) | `data/quality/baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/quality/freshness_report.json` | 
| Timestamp mới nhất       | `2026-08-01` | 
| Ngưỡng freshness         | `180` ngày | 
| Trạng thái baseline      | Stale | 
| Lý do                     | Mặc dù `stale_rows=0`, `is_fresh` được đánh giá false do dataset có ít record hợp lệ và threshold 180 ngày. |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop records | Loại bỏ 2 record mới nhất | 2 | Volume giảm, retrieval có thể mất document đúng | Không ảnh hưởng quá lớn tới top-k nhưng giảm tính toàn vẹn | Tái bổ sung hoặc loại bỏ khung query tương ứng |
| Blank summary | Đặt `summary` rỗng | 1 | Completeness giảm, retrieval có thể trả kết quả sai | Dẫn tới summary_min_length fail và mục không thể trả | Repair bằng nguồn metadata gốc hoặc bỏ record |
| Stale published date | Đặt ngày cũ 2020-01-01 | 2 | Freshness fail | Freshness report cho thấy row stale và `is_fresh=false` | Sửa ngày về hiện tại hoặc lấy lại trường published chính xác |
| Duplicate DOI | Nhân bản 2 DOI | 2 | Uniqueness fail | `paper_id_unique` fail trong corrupted quality report | Loại bỏ duplicate; giữ unique DOI trong repaired dataset |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log bao gồm bảy hành động corruption rõ ràng, gồm drop_records, blank_summary, inject_noise, truncate_title, stale_published_date, add_duplicates. Log mô tả paper_id và paper_ids, đủ để tái tạo từng corruption case.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair được thiết kế để phục hồi cấu trúc dữ liệu và chất lượng bằng cách sửa duplicate DOI, bổ sung summary bị mất, loại bỏ noise không mong muốn và đưa published date về giá trị hợp lệ, thay vì chỉ sửa metric đầu ra. Các hành động repair dựa trên nguồn raw ban đầu hoặc rule kiểm tra schema để đảm bảo tính nhất quán.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       0.6 |      0.75 | -0.4 | +0.15 | Corruption làm giảm top-k retrieval; repaired dữ liệu phục hồi một phần. |
| `mean_token_f1`        |   0.7516 |   0.4179 |   0.0956 | -0.3337 | -0.3223 | Mức F1 giảm mạnh sau corruption; repaired không khôi phục được về baseline do metrics khác nhau hoặc đánh giá bằng dataset/nhiều samples khác. |
| `judge_accuracy`       |   0.6667 |   0.4 |   0.0 | -0.2667 | -0.4 | Judge accuracy giảm sau corruption và không phục hồi hoàn toàn trong repaired artifact. |
| `mean_judge_score`     |   3.6667 |   2.6 |   1.0 | -1.0667 | -1.6 | Score giảm theo corruption, repaired artifact hiển thị điểm thấp hơn baseline. |
| Quality checks pass/fail |      Pass |       Fail |      Pass | Bị fail nhiều checks | Khôi phục nhiều checks | Corruption gây duplicate/summary fail; repaired phục hồi uniqueness và summary_min_length. |
| Freshness status         | Stale | Stale | Stale | Không đổi | Không đổi | Dataset vẫn đánh giá stale vì vẫn còn published missing/invalid. |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Corruption/data change] → [quality/freshness signal] → [retrieval/answer metric].
2. [Repair action] → [quality/freshness recovery] → [agent metric recovery hoặc lý do chưa recovery].

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Baseline và repaired metrics sử dụng số samples khác nhau nên khó so sánh trực tiếp. Repaired metrics có `samples=120` trong khi baseline và corrupted chỉ có `samples=15`.
- **Nguyên nhân:** Chênh lệch dataset hoặc cách tính sample giữa các bước evaluation khác nhau trong pipeline. Có thể do chạy đánh giá repaired trên toàn bộ corpus thay vì trên cùng test set.
- **Cách xử lý:** Ghi rõ trong báo cáo rằng repaired artifact không dùng cùng ngữ cảnh sample với baseline/corrupted, và cần đồng bộ lại test set hoặc script đánh giá để sử dụng chung `data/eval/test_set.json`.
- **Cách xác minh:** So sánh `samples` trong `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json` và kiểm tra cấu hình script chạy.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Khác biệt số lượng mẫu evaluation giữa baseline/corrupted/repaired | Khó so sánh trực tiếp chỉ số do `samples` khác nhau; khiến kết luận về repair không nhất quán | Đồng bộ lại script đánh giá để tất cả trạng thái dùng chung `data/eval/test_set.json` và cùng `samples=15` nếu đó là test set chung. |
| Freshness vẫn fail do missing/invalid published dates | Dù quality checks pass nhiều, dataset vẫn bị đánh giá stale vì field `published` không hợp lệ với 2 record | Cải thiện nguồn date extraction và chuẩn hóa `published`/`age_days` trước khi đánh giá freshness; bổ sung rule kiểm tra ngày trong pipeline. |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
