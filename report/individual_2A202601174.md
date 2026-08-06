# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Thanh Bình |
| MSSV | 2A202601174 |
| Khóa/Lớp | K4 |
| Tên nhóm | A8 |
| Vai trò chính | Integration & Comparison |
| Repository | https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Baseline integration | `src/pipelines/phase1.py` — `main`, validation và artifact helpers | Raw Crossref snapshot cùng các module cleaning, index, evaluation và observability | Clean artifacts, baseline index, answers, metrics, quality/freshness và `phase1_report.md` | Hoàn thành, đã chạy end-to-end |
| Corruption/repair comparison | `src/pipelines/corruption_flow.py` — `main` và các preflight helpers | Baseline artifacts, frozen test set, corruption function và raw snapshot | Corrupted/repaired datasets, indexes, answers, metrics, quality/freshness và `corruption_report.md` | Hoàn thành, đã chạy end-to-end |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Rà soát contract tích hợp | Ingestion, cleaning, retrieval, evaluation và observability | Xác nhận chữ ký hàm, schema và đường dẫn artifact trước khi orchestration |
| Kiểm tra bằng chứng đầu ra | Corruption và observability | Đối chiếu corruption log, quality/freshness signals và metric delta trong comparison report |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Tích hợp baseline raw → clean → index → evaluate → observe → report | `src/pipelines/phase1.py` | 24 clean records, 15 evaluation samples, baseline retrieval hit rate `1.0000` | `.venv/bin/python script/run_phase1.py` và `data/results/baseline_metrics.json` |
| Validate frozen test set với clean corpus | `_validate_test_set` | Phát hiện sớm sample thiếu field, duplicate ID hoặc ground-truth document ID không tồn tại | Baseline flow hoàn thành với 15/15 sample hợp lệ |
| Bảo vệ artifact theo ba trạng thái | `_ensure_separate_state_paths` | Baseline, corrupted và repaired dùng JSON, manifest, metrics và answers paths riêng | Ba manifest và ba bộ metrics tồn tại độc lập trong `data/` |
| Điều phối corruption và rebuild index | `src/pipelines/corruption_flow.py` | Corrupted retrieval hit rate giảm từ `1.0000` xuống `0.6000` | `data/results/corrupted_metrics.json` |
| Repair từ raw snapshot và so sánh | `src/pipelines/corruption_flow.py` | Repaired retrieval hit rate phục hồi về `1.0000`; comparison report có delta | `data/results/repaired_metrics.json` và `data/reports/corruption_report.md` |

Output tiêu biểu là `data/reports/corruption_report.md`. Báo cáo chứng minh cùng một test set có retrieval hit rate `1.0000 → 0.6000 → 1.0000`, đồng thời token F1, judge accuracy và mean judge score cũng giảm rồi phục hồi.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Hai pipeline cần kết nối các module do nhiều thành viên thực hiện thành một luồng tái lập được. Việc tích hợp phải tránh ghi đè baseline, không được thay test set giữa ba trạng thái và chỉ được repair từ raw snapshot đáng tin cậy. Nếu contract hoặc artifact sai, pipeline phải dừng sớm với lỗi có thể hành động thay vì tạo comparison không hợp lệ.

### Cách triển khai

Trong baseline flow, pipeline ưu tiên raw snapshot đã lưu, trừ khi cấu hình yêu cầu refresh. Dữ liệu được clean và ghi CSV/JSON, sau đó tạo collection `papers-baseline`. Test set được tạo hoặc nạp lại, rồi validate schema, sample ID, ground-truth IDs và sự tồn tại của các document trong clean corpus. Pipeline tiếp tục evaluate, chạy quality/freshness checks và tạo báo cáo từ artifact thật.

Trong corruption flow, preflight kiểm tra đủ baseline artifacts và bảo đảm đường dẫn ba trạng thái khác nhau. Pipeline nạp clean baseline cùng metrics/test set đã khóa, tạo corrupted dataframe có log, tạo collection `papers-corrupted` và evaluate lại. Repair không chỉnh tay corrupted data mà nạp lại `crossref_records.json`, chạy cleaning, tạo collection `papers-repaired`, evaluate bằng chính test set cũ và sinh comparison report.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_records.json`, baseline clean JSON, frozen `data/eval/test_set.json`, baseline metrics và các hàm của module phụ thuộc |
| Output | Clean/corrupted/repaired CSV/JSON, ba embedding manifests/collections, answers, metrics, quality/freshness artifacts và hai Markdown reports |
| Module phụ thuộc | `ingestion.crossref`, `ingestion.cleaning`, `ingestion.corruption`, `retrieval.index`, `evaluation.metrics`, `evaluation.testset`, `observability.quality`, `observability.reporting` |
| Module sử dụng output | Hai script entrypoint, báo cáo nhóm/cá nhân và phần demo cuối |
| Điều kiện lỗi cần xử lý | Thiếu baseline artifact, empty dataset, malformed test set, ground-truth ID không tồn tại, metrics/test-set sample count lệch hoặc ba trạng thái dùng trùng path |

### Cách xác minh

```bash
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_TOKEN= HUGGING_FACE_HUB_TOKEN= HUGGINGFACEHUB_API_TOKEN= .venv/bin/python script/run_phase1.py
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_TOKEN= HUGGING_FACE_HUB_TOKEN= HUGGINGFACEHUB_API_TOKEN= .venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline chạy xong; corruption làm metrics/signals xấu đi; repair từ raw phục hồi các metric bị ảnh hưởng; artifacts ba trạng thái tách biệt.
- **Kết quả thực tế:** Baseline tạo 24 records và 15 samples. Corruption flow hoàn thành với retrieval hit rate `1.0000 → 0.6000 → 1.0000`.
- **Artifact/log:** `data/results/corruption_log.json`, ba file metrics trong `data/results/`, quality/freshness trong `data/quality/`, và reports trong `data/reports/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Corrupted và repaired evaluation chỉ có ý nghĩa khi so sánh trên cùng câu hỏi, ground truth, evaluator và retrieval configuration.
- **Các phương án đã cân nhắc:** Tạo lại test set cho mỗi trạng thái; hoặc khóa test set baseline và validate nó trước mọi lần evaluate.
- **Phương án đã chọn:** Dùng một frozen `test_set.json`, validate sample count và ground-truth IDs, đồng thời dùng paths/collection names riêng cho baseline, corrupted và repaired.
- **Lý do:** Tạo lại test set có thể đổi paper, câu hỏi hoặc UUID, làm metric delta không còn là so sánh cùng điều kiện. Frozen test set tăng correctness và reproducibility với độ phức tạp thấp.
- **Bằng chứng quyết định phù hợp:** Cả ba metrics artifacts có đúng 15 samples; retrieval hit rate thay đổi `-0.4000` sau corruption và `+0.4000` sau repair. Baseline metrics không bị ghi đè.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `401 Unauthorized` và `OAuth token signature verification failed` khi tải public model `sentence-transformers/all-MiniLM-L6-v2`.
- **Lệnh hoặc bước tái hiện:** Chạy `.venv/bin/python script/run_phase1.py` trong môi trường hiện tại.
- **Nguyên nhân gốc:** Máy tự động gắn một Hugging Face OAuth token đã cache nhưng chữ ký không còn hợp lệ, dù model là public. Lần chạy trong sandbox còn bị chặn DNS trước khi cho phép network.
- **Cách xử lý:** Cho phép network cho bước tải model và đặt `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` để tải public artifact không dùng cached token. Không sửa hoặc ghi token vào source/report.
- **Cách xác minh sau khi sửa:** Baseline exit code `0`; corruption flow exit code `0` và in `retrieval_hit_rate 1.0000 -> 0.6000 -> 1.0000`.
- **Điều học được:** Lỗi authentication của dependency bên ngoài cần được tách khỏi lỗi orchestration; traceback và bước chạy độc lập giúp xác định đúng boundary.

## 7. Hiểu biết về luồng end-to-end

1. Crossref payload được lưu nguyên bản, parse thành `PaperRecord`, rồi cleaning chuẩn hóa title, summary, authors, categories, publication date, `age_days` và `text_for_embedding`. Clean dataframe được embed bằng MiniLM và nạp vào Chroma collection.
2. Evaluation set lưu câu hỏi, ground truth và `ground_truth_doc_ids`. Retrieval hit xảy ra khi ít nhất một retrieved document ID nằm trong danh sách ground-truth IDs; câu trả lời được đo thêm bằng token F1 và judge metrics.
3. Quality checks kiểm tra volume, schema, completeness, uniqueness và validity tại cấp record. Freshness monitoring tập trung vào tuổi dữ liệu, publication range, stale/missing/future dates và độ nhất quán giữa date với `age_days`.
4. Phải dùng cùng test set để metric delta phản ánh thay đổi của dữ liệu/index thay vì thay đổi câu hỏi hoặc ground truth.
5. Repair thành công khi repaired data được dựng lại từ raw, corruption-specific signals phục hồi và agent metrics quay về baseline. Trong lần chạy này, agent metrics phục hồi hoàn toàn; quality tổng thể vẫn FAIL vì raw baseline vốn có hai record thiếu publication date.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | Giảm 0.4000 và phục hồi hoàn toàn |
| `mean_token_f1` | 0.7516 | 0.4179 | 0.7516 | Data corruption làm answer overlap giảm rõ rệt |
| `judge_accuracy` | 0.6667 | 0.4000 | 0.6667 | Giảm 0.2667 rồi quay lại baseline |
| `mean_judge_score` | 3.6667 | 2.6000 | 3.6667 | Giảm 1.0667 rồi phục hồi hoàn toàn |
| Quality checks | FAIL — 9 pass/2 fail | FAIL — 5 pass/6 fail | FAIL — 9 pass/2 fail | Corruption-specific failures được repair; hai lỗi nguồn baseline còn lại |
| Freshness status | FAIL — 0 stale, 2 missing | FAIL — 3 stale, 5 missing | FAIL — 0 stale, 2 missing | Staleness và missing tăng sau corruption rồi trở về baseline |

### Kết luận từ số liệu

1. Drop hai latest records cùng blank/noisy summaries, truncated title, stale dates và duplicates → quality failed checks tăng `2 → 6`, stale rows tăng `0 → 3` → retrieval hit rate giảm `1.0000 → 0.6000`, token F1 giảm `0.7516 → 0.4179`.
2. Re-clean từ raw snapshot và rebuild collection → failed checks giảm `6 → 2`, stale rows giảm `3 → 0` → retrieval hit rate và toàn bộ answer/judge metrics quay lại đúng baseline.

Corruption ảnh hưởng rõ nhất tới retrieval là drop hai latest papers có trong frozen test set. Mỗi paper đó có ba câu hỏi, nên sáu trong 15 samples mất ground-truth document; retrieval hit rate giảm đúng từ 15/15 xuống 9/15, tức `0.6000`. Blank/noisy summary và title truncation còn làm answer quality giảm.

Kết quả khác kỳ vọng là repaired quality và freshness vẫn mang trạng thái FAIL thay vì PASS. Đối chiếu artifacts cho thấy repaired data đã trở về đúng baseline, nhưng raw source ban đầu có hai record thiếu publication date, tạo `age_days=-1`. Vì vậy repair được kết luận là phục hồi hoàn toàn corruption-specific damage và agent metrics, nhưng không sửa được lỗi vốn có trong nguồn baseline.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Integration cần preflight contracts và artifact isolation; chỉ gọi đúng thứ tự chưa đủ để bảo đảm comparison hợp lệ.
2. Một trạng thái tổng thể FAIL vẫn cần đọc signal chi tiết: repaired FAIL không đồng nghĩa repair thất bại nếu nó đã trở về đúng mức baseline.
3. Mất ground-truth documents trong corpus tác động trực tiếp tới retrieval và kéo theo token F1/judge metrics, cho thấy data quality là một phần của chất lượng RAG.

### Nếu có thêm thời gian

Tôi sẽ thêm một baseline acceptance gate cho publication date: hoặc loại record thiếu ngày với logged reason, hoặc dùng một policy fallback có nguồn rõ ràng. Cải thiện được đo bằng `published_date_valid`, `age_days_valid` và freshness chuyển PASS mà không làm giảm số evaluation ground-truth documents. Tôi cũng sẽ lưu hash của frozen test set trong comparison report để chứng minh ba lần evaluate dùng đúng cùng artifact.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Thanh Bình
**Ngày xác nhận:** 2026-08-06
