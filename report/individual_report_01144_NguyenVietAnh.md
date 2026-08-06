# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Họ và tên       | Nguyễn Việt Anh                                                                                                                                |
| MSSV               | 2A202601144                                                                                                                                      |
| Khóa/Lớp         | K4                                                                                                                                               |
| Tên nhóm         | My3Mien                                                                                                                                          |
| Vai trò chính    | Data Engineer                                                                                                                                    |
| Repository         | [github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability](https://github.com/doclautc-1808/K4_Day10_Data-Pipeline-Data-Observability)  |
| Ngày hoàn thành | 2026-08-06                                                                                                                                       |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable   | File/hàm phụ trách         | Input nhận vào                      | Output bàn giao                                        | Trạng thái |
| -------------------- | ----------------------------- | ------------------------------------- | ------------------------------------------------------- | ------------ |
| Tải dữ liệu API   | `src/ingestion/crossref.py` | Cấu hình`Settings` (Query/Filter) | File`raw_records.json`                                | Hoàn thành |
| Làm sạch dữ liệu | `src/ingestion/cleaning.py` | `list[PaperRecord]` từ file raw    | File`papers_clean.csv`, `papers_clean.json`         | Hoàn thành |
| Sinh tập kiểm thử | `src/evaluation/testset.py` | `pd.DataFrame` dữ liệu sạch      | File`test_set.json` (Gồm câu hỏi và ground truth) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động               | Thành viên/module được hỗ trợ | Kết quả                                                                                                            |
| -------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Phân tích lỗi dữ liệu | Data Engineer & System               | Phát hiện nguyên nhân cột`categories_joined` bị trống do API Crossref không trả về trường `subject`. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan                    | Kết quả bàn giao                                       | Cách xác minh                            |
| --------------------------- | ------------------------------------------------ | --------------------------------------------------------- | ------------------------------------------ |
| Lấy dữ liệu API & Clean  | `crossref_records.json`, `papers_clean.json` | Tải thành công 24 records, làm sạch 24 dòng         | `python script/run_clean_and_testset.py` |
| Tạo bộ Evaluation Set     | `test_set.json`                                | Sinh ra 15 câu hỏi (summary, authors, date, categories) | `python script/run_clean_and_testset.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Pipeline tải tự động 24 records dữ liệu báo khoa học, sinh ra Dataframe chuẩn hóa và 15 câu hỏi evaluation set để đánh giá LLM.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Lấy tự động siêu dữ liệu (metadata) của các bài báo khoa học từ Crossref API, chuẩn hóa các trường dữ liệu để hỗ trợ tạo embedding và sinh bộ test case tự động phục vụ quá trình đánh giá mô hình RAG.

### Cách triển khai

- Sử dụng thư viện `requests` để gọi API kết hợp với hàm `_request_with_retry` (custom retry logic) xử lý lỗi 429/503.
- Xử lý mảng tác giả và chuyên mục thành dạng chuỗi text phẳng, làm sạch mã HTML trong phần `abstract` để sinh ra file CSV/JSON bằng `pandas`.
- Tại bước tạo test set, lấy top 5 bản ghi và sử dụng `uuid` để tạo các ID câu hỏi không trùng lặp cho các loại `summary`, `authors`, `date`, `categories`.

### Input, output và contract

| Thành phần                   | Mô tả                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| Input                          | Metadata JSON từ Crossref (24 items).                                                      |
| Output                         | `papers_clean.json` (Dữ liệu sạch) và `test_set.json` (Bộ kiểm thử đánh giá). |
| Module phụ thuộc             | `core.config.Settings`, thư viện `requests`, `pandas`.                              |
| Module sử dụng output        | Module nhúng (Embedding / ChromaDB) và pipeline đánh giá (Evaluation).                 |
| Điều kiện lỗi cần xử lý | Xử lý lỗi API rate limit, dữ liệu`subject` rỗng, `published` bị thiếu.          |

### Cách xác minh

```bash
python script/run_clean_and_testset.py
```

- **Kết quả mong đợi:** In ra log báo hoàn thành việc tải API, lưu file dữ liệu sạch, và sinh ra test set thành công.
- **Kết quả thực tế:** Hệ thống báo tải 24 records, làm sạch 24 dòng, sinh ra 15 câu hỏi test.
- **Artifact/log:** File được tạo ở `data/clean/papers_clean.json` và `data/eval/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Thuộc tính categories trả về từ Crossref API có thể rỗng hoặc hoàn toàn không tồn tại đối với nhiều bài báo khoa học.
- **Các phương án đã cân nhắc:**
  - 1. Báo lỗi và dừng pipeline nếu không có danh mục.
    2. Dùng hàm get an toàn `item.get("subject", [])` để gán mảng rỗng.
- **Phương án đã chọn:** Dùng hàm get an toàn với giá trị mặc định là `[]`.
- **Lý do:** Giúp data pipeline tăng tính chịu lỗi, không bị crash giữa chừng vì dữ liệu thực tế thường xuyên khuyết thiếu một số trường.
- **Bằng chứng quyết định phù hợp:** Script chạy thành công hoàn toàn mà không văng Exception dù 100% bản ghi thiếu trường `subject`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Cột `categories_joined` xuất hiện trong data làm sạch nhưng ở 100% bản ghi đều mang chuỗi rỗng `""`.
- **Lệnh hoặc bước tái hiện:** Kiểm tra file `data/clean/papers_clean.json`.
- **Nguyên nhân gốc:** Crossref API thực sự không trả về trường `"subject"` cho nhóm bài báo được truy vấn (do metadata gốc thiếu).
- **Cách xử lý:** Duyệt trực tiếp file raw payload gốc `crossref_response.json` (bằng đoạn mã python check) để xác nhận có 0 items chứa `subject`. Từ đó kết luận là do dữ liệu nguồn, chứ không phải lỗi xử lý code. Giữ nguyên phương pháp get an toàn.
- **Cách xác minh sau khi sửa:** Check raw payload: `len(items) == 24` nhưng count `subject` == 0.
- **Điều học được:** Data schema mong muốn không phải lúc nào cũng được Source cung cấp đầy đủ. Cần kỹ năng đối chiếu (verify) raw source thay vì lập tức sửa code logic khi thấy data trống.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu được tải dạng raw JSON -> `crossref.py` lọc lấy thông tin cần thiết -> `cleaning.py` loại bỏ HTML, nối tác giả, tính tuổi ngày xuất bản -> Xuất ra `.csv`/`.json` -> `index.py` đọc `.json`, dùng `sentence-transformers` tạo vector nhúng (embedding) -> Lưu vào ChromaDB.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   `ground_truth` dùng đối chiếu với câu trả lời của AI để đo độ chính xác (Generation Quality). `ground_truth_doc_ids` dùng kiểm tra các chunk mà ChromaDB truy xuất (retrieve) được có chứa bài báo gốc hay không (đo Retrieval Hit Rate).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks quan tâm tới "sự đầy đủ/đúng đắn của cấu trúc" (VD: title không được rỗng, author phải định dạng đúng). Freshness monitoring quan tâm tới "độ mới của dữ liệu" (VD: Ngày xuất bản `age_days` không được quá ngưỡng 180 ngày).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để duy trì tính công bằng (apple-to-apple comparison). Nếu đổi câu hỏi test set, độ khó thay đổi sẽ khiến ta không thể kết luận performance giảm là do dữ liệu xấu đi (corruption) hay do câu hỏi mới khó hơn.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Thành công khi các metrics như `retrieval_hit_rate` và `mean_token_f1` ở file `repaired_metrics.json` tăng trở lại và đạt mức tương đương hoặc bằng `baseline_metrics.json`.

## 8. Phân tích kết quả

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

1. Việc xây dựng pipeline không chỉ là fetch API, mà cốt lõi nằm ở bước cleaning (xử lý schema, text, date) để dữ liệu thân thiện nhất với các mô hình Vector nhúng sau này.
2. Thiết kế hệ thống đánh giá tự động (Test set có sẵn `ground_truth` và `doc_ids`) giúp tiết kiệm thời gian đáng kể trong quá trình đo lường vòng lặp RAG.
3. Observability rất quan trọng. Khi chất lượng dữ liệu nền tảng giảm (Data Corruption), hiệu năng của Agent (Generation Quality) sẽ giảm theo. RAG chỉ thông minh khi Data sạch.

### Nếu có thêm thời gian

Sẽ tích hợp Pydantic để thực hiện Data Validation chặt chẽ hơn ngay khi parse dữ liệu từ Crossref API. Pydantic giúp tự động ép kiểu và văng exception chi tiết nếu có schema bất thường, từ đó nâng cao độ tin cậy của Data Pipeline từ pha đầu vào.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Việt Anh
**Ngày xác nhận:** 2026-08-06
