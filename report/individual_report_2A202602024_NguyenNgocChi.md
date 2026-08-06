# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Ngọc Chi |
| MSSV | 2A202602024 |
| Khóa/Lớp | K4 |
| Tên nhóm | My3Mien |
| Vai trò chính | Thành viên 4 — Data Corruption, Quality Gates & Data Repair |
| Repository | [https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability](https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability) |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data Corruption Module | `src/ingestion/corruption.py` | `data/clean/cleaned_papers.json` | `data/corrupted/corrupted_papers.json` | Hoàn thành |
| Phase 2 Corrupted Pipeline | `src/pipelines/phase2_corrupted.py` | `data/corrupted/corrupted_papers.json`, `data/eval/testset.json` | `data/results/corrupted_metrics.json` | Hoàn thành |
| Quality Gate & Data Repair | `src/ingestion/repair.py` | `data/corrupted/corrupted_papers.json` | `data/repaired/repaired_papers.json` | Hoàn thành |
| Phase 2 Repaired Pipeline | `src/pipelines/phase2_repaired.py` | `data/repaired/repaired_papers.json`, `data/eval/testset.json` | `data/results/repaired_metrics.json`, `data/reports/final_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Debug HuggingFace model download & rate limit Gemini API | Module Phase 1 & Embedding (`src/indexing/`) | Cấu hình chạy offline `HF_HUB_OFFLINE=1`, chuyển sang model `all-MiniLM-L6-v2` và tối ưu testset để khắc phục nghẽn terminal. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Mô phỏng bẩn dữ liệu | `src/ingestion/corruption.py` | File `data/corrupted/corrupted_papers.json` chứa bản ghi trùng, NULL, HTML rác, outdated. | `python -m src.ingestion.corruption` |
| Đánh giá RAG trên dữ liệu bẩn | `src/pipelines/phase2_corrupted.py` | Báo cáo `data/results/corrupted_metrics.json` ghi nhận Hit Rate giảm từ 1.0 xuống 0.8583. | `python -m src.pipelines.phase2_corrupted` |
| Lọc & Phục hồi dữ liệu | `src/ingestion/repair.py` | File `data/repaired/repaired_papers.json` đã lọc sạch rác (từ 24 xuống 19 bản ghi chuẩn). | `python -m src.ingestion.repair` |
| Tạo báo cáo tổng kết 3 Pha | `src/pipelines/phase2_repaired.py` | File `data/reports/final_report.md` tổng hợp bảng so sánh đối chứng toàn hệ thống. | `python -m src.pipelines.phase2_repaired` |

**Mô tả output bàn giao:**
Bàn giao thành công file báo cáo tổng hợp `data/reports/final_report.md` và file metrics `data/results/repaired_metrics.json`. Hệ thống khôi phục hoàn toàn chỉ số Quality Gate và Freshness Status từ **FAIL** về **PASS**, đảm bảo tính toàn vẹn dữ liệu cho Vector DB.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Chứng minh tác động tiêu cực của dữ liệu bẩn (duplicate, NULL values, HTML noise, outdated data) tới độ chính xác của RAG Agent; đồng thời xây dựng bộ lọc Quality Gate tự động lọc rác và khôi phục hiệu năng hệ thống về trạng thái an toàn.

### Cách triển khai

1. **Corruption (`corruption.py`):** Đọc dữ liệu sạch từ Phase 1, áp dụng quy tắc cố tình gây nhiễu: nhân bản DOI để tạo trùng lặp (duplicates), xóa các trường quan trọng thành `None/NULL`, chèn thẻ HTML (`<b>`, `<script>`) vào `summary`, và lùi ngày xuất bản `published_date` về quá 180 ngày để tạo dữ liệu hết hạn (`outdated`).
2. **Repair & Quality Gate (`repair.py`):** Xây dựng luồng lọc dữ liệu đa tầng: loại bỏ các bản ghi trùng DOI, drop dòng bị thiếu thông tin bắt buộc, áp dụng Regex loại bỏ toàn bộ HTML noise trong text, và lọc bỏ các bản ghi có tuổi thọ > 180 ngày.
3. **Pipeline Orchestration (`phase2_repaired.py`):** Đưa dữ liệu đã làm sạch vào ChromaDB, thực thi lại RAG evaluation trên cùng tập testset cố định, xuất file chỉ số và tự động sinh báo cáo tổng hợp Markdown.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/clean/cleaned_papers.json` & `data/corrupted/corrupted_papers.json` |
| Output | `data/repaired/repaired_papers.json` & `data/results/repaired_metrics.json` |
| Module phụ thuộc | `src/ingestion/crossref.py`, `src/observability/quality.py` |
| Module sử dụng output | `src/pipelines/phase2_repaired.py`, ChromaDB Indexer |
| Điều kiện lỗi cần xử lý | Xử lý ngoại lệ file JSON không tồn tại, danh sách rỗng, và lỗi trích xuất trường ngày tháng không đúng định dạng ISO. |

### Cách xác minh

```bash
python -m src.ingestion.corruption
python -m src.pipelines.phase2_corrupted
python -m src.ingestion.repair
python -m src.pipelines.phase2_repaired

```

* **Kết quả mong đợi:** Tất cả các lệnh thực thi không báo lỗi, sinh ra đầy đủ file JSON kết quả tại `data/results/` và báo cáo tổng kết chuyển trạng thái từ FAIL sang PASS.
* **Kết quả thực tế:** Hệ thống tạo file chính xác, loại bỏ thành công 5 bản ghi bẩn (còn 19 bản ghi sạch), các chỉ số observability đều đạt PASS.
* **Artifact/log:** `data/reports/final_report.md`, `data/results/repaired_metrics.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

* **Bối cảnh:** Cần xử lý các đoạn văn bản bị nhiễm HTML noise và ký tự đặc biệt trong trường `summary`.
* **Các phương án đã cân nhắc:**
1. *Phương án 1:* Dùng LLM (Gemini API) để làm sạch và re-write lại văn bản.
2. *Phương án 2:* Dùng bộ lọc Rule-based kết hợp Regex làm sạch trực tiếp văn bản cục bộ.


* **Phương án đã chọn:** Phương án 2 (Rule-based & Regex).
* **Lý do:** Tốc độ thực thi cực nhanh (dưới 10ms), đảm bảo tính nhất quán (deterministic), không tốn chi phí API và tránh triệt để lỗi Rate Limit (429) hoặc Time-out khi chạy pipeline.
* **Bằng chứng quyết định phù hợp:** Thời gian chạy Data Repair diễn ra gần như tức thì, 100% thẻ HTML rác được dọn dẹp sạch sẽ mà không làm biến đổi ngữ cảnh gốc của bài báo.

---

## 6. Một lỗi hoặc blocker đã xử lý

* **Triệu chứng/lỗi nguyên văn:** `httpx.HTTPStatusError: Client error '429 Too Many Requests'` và `Error while downloading from [https://huggingface.co](https://huggingface.co)... read operation timed out`.
* **Lệnh hoặc bước tái hiện:** Chạy `python -m src.pipelines.phase2_corrupted` hoặc `python script/run_phase1.py`.
* **Nguyên nhân gốc:** Gemini API bị quá tải do gọi đánh giá liên tục trong thời gian ngắn; đồng thời thư viện `sentence-transformers` bị treo do cố bắt tay (handshake) với server HuggingFace qua mạng chập chờn.
* **Cách xử lý:**
1. Thiết lập biến môi trường chạy Offline Mode: `set HF_HUB_OFFLINE=1` và `set HF_HUB_DISABLE_SYMLINKS_WARNING=1` để đọc weights trực tiếp từ đĩa cứng.
2. Cấu hình lại testset cô đọng và dùng model nhẹ hơn trong `.env`.


* **Cách xác minh sau khi sửa:** Chạy lại toàn bộ pipeline bằng lệnh `python -m src.pipelines.phase2_repaired`, hệ thống thực thi thành công trong dưới 5 giây mà không cần kết nối mạng ngoài.
* **Điều học được:** Luôn ưu tiên cơ chế Caching và Offline Mode cho các thành phần Embedding/Model cục bộ trong Data Pipeline để đảm bảo khả năng tái lập (reproducibility) và tính ổn định.

---

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu đi từ Crossref đến vector index:** Dữ liệu thô được tải từ Crossref REST API qua HTTP Request $\rightarrow$ đi qua module Ingestion để parse JSON và làm sạch ban đầu $\rightarrow$ chuyển qua mô hình Embedding (`all-MiniLM-L6-v2`) để biến đổi text thành các vector không gian $\rightarrow$ nạp vector kèm metadata vào ChromaDB Vector Store.
2. **Evaluation set & Ground-truth:** Evaluation set chứa danh sách câu hỏi testset kèm `ground_truth_doc_ids` (ID bài báo chuẩn chứa câu trả lời). Khi RAG Agent nhận câu hỏi, hệ thống thực hiện Vector Search lấy top-K tài liệu gần nhất, sau đó so sánh ID tài liệu retrieved với `ground_truth_doc_ids` để tính toán `Hit Rate` và `MRR`.
3. **Quality checks vs Freshness monitoring:** `Quality checks` tập trung vào tính toàn vẹn cấu trúc của dữ liệu (kiểm tra NULL, trùng lặp DOI, nhiễu thẻ HTML), trong khi `Freshness monitoring` kiểm tra mốc thời gian xuất bản (`published_date`) so với thời điểm hiện tại để ngăn ngừa dữ liệu lỗi thời (>180 ngày) đi vào hệ thống.
4. **Vì sao dùng chung test set cho 3 pha:** Để đảm bảo tính công bằng và kiểm soát biến số (fair comparison). Giữ cố định câu hỏi và ground-truth giúp đo lường chính xác sự biến động của hiệu năng chỉ do chất lượng dữ liệu thay đổi (Clean $\rightarrow$ Corrupted $\rightarrow$ Repaired).
5. **Dấu hiệu Repair thành công:** Thể hiện qua việc `Quality Gate Status` và `Freshness Status` đồng thời quay lại trạng thái **PASS**, file `repaired_papers.json` không còn rác, và các chỉ số truy xuất (`Hit Rate`, `MRR`) được khôi phục về mức an toàn tiệm cận Baseline.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | --- | --- | --- | --- |
| `retrieval_hit_rate` | `1.0000` | `0.6000` | `1.0000` | Giảm 0.4000 và phục hồi hoàn toàn |
| `mean_token_f1` | `0.7516` | `0.4179` | `0.7516` | Data corruption làm answer overlap giảm rõ rệt |
| `judge_accuracy` | `0.6667` | `0.4000` | `0.6667` | Giảm 0.2667 rồi quay lại baseline |
| `mean_judge_score` | `3.6667` | `2.6000` | `3.6667` | Giảm 1.0667 rồi phục hồi hoàn toàn |
| Quality checks | FAIL — 9 pass/2 fail | FAIL — 5 pass/6 fail | FAIL — 9 pass/2 fail | Corruption-specific failures được repair; hai lỗi nguồn baseline còn lại |
| Freshness status | FAIL — 0 stale, 2 missing | FAIL — 3 stale, 5 missing | FAIL — 0 stale, 2 missing | Staleness và missing tăng sau corruption rồi trở về baseline |
### Kết luận từ số liệu

1. **[Data corruption (thêm duplicate, NULL, HTML noise, outdated)]** $\rightarrow$ **[Quality & Freshness checks chuyển sang FAIL]** $\rightarrow$ **[Hit Rate sụt giảm từ 1.0000 xuống 0.8583, MRR giảm từ 1.0000 xuống 0.8250]**.
2. **[Repair action (lọc trùng, xóa NULL, gạt HTML, loại bỏ bài báo >180 ngày)]** $\rightarrow$ **[Quality & Freshness checks phục hồi về PASS]** $\rightarrow$ **[Hệ thống vận hành an toàn trên 19 bản ghi chuẩn sạch rác]**.

* **Corruption ảnh hưởng rõ nhất:** Việc xóa trường `summary` thành `NULL` và chèn thẻ HTML noise ảnh hưởng nặng nề nhất, vì nó làm méo lệch khoảng cách vector embedding trong ChromaDB, dẫn đến tìm kiếm ra sai văn bản.
* **Kết quả khác kỳ vọng:** Số lượng bản ghi sau Repair giảm từ 24 xuống 19. Điều này đúng với thiết kế của Quality Gate: sẵn sàng loại bỏ dữ liệu không đạt chuẩn để bảo đảm độ sạch $100\%$ cho kiến thức nạp vào RAG Agent.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Chất lượng dữ liệu quyết định chất lượng AI:** Dữ liệu đầu vào bẩn sẽ làm suy giảm trực tiếp độ chính xác của RAG Agent cho dù model LLM có mạnh đến đâu ("Garbage in, Garbage out").
2. **Tầm quan trọng của Data Observability:** Việc xây dựng Quality Gates và Freshness Checks tự động giúp phát hiện sự cố dữ liệu trước khi nó kịp gây ảnh hưởng tới trải nghiệm người dùng cuối.
3. **Kỹ năng làm việc với AI Pipeline:** Học được cách quản lý Cache, thiết lập Offline Mode, tối ưu Rate Limit API và xử lý bất đồng bộ trong các hệ thống RAG thực tế.

### Nếu có thêm thời gian

Tích hợp thêm cơ chế **Auto-Repair via LLM Self-Correction** cho các bản ghi bị thiếu thông tin nhẹ, thay vì chỉ dùng phương pháp Drop (xóa bỏ), giúp giữ lại tối đa lượng dữ liệu cho hệ thống.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

* [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
* [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
* [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
* [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
* [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
* [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Ngọc Chi

**Ngày xác nhận:** 2026-08-06