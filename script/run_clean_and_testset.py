import sys
from pathlib import Path

# Add src to python path so it can import the project packages
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from datetime import datetime, UTC
from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set

def main():
    # Load settings which contains all the paths and configurations
    settings = load_settings()
    
    # 1. Load Raw Records
    raw_path = settings.paths.raw_records_json
    print(f"[*] Đang tải dữ liệu raw từ: {raw_path}")
    
    try:
        records = load_raw_records(raw_path)
        print(f"   -> Đã tải thành công {len(records)} records.")
    except Exception as e:
        print(f"[!] Lỗi khi load raw records: {e}")
        return

    # 2. Clean Data
    print("\n[*] Đang xử lý làm sạch dữ liệu (Cleaning)...")
    run_date = datetime.now(UTC)
    df = build_clean_dataframe(records, run_date)
    
    print(f"   -> Dữ liệu sau khi làm sạch: {len(df)} dòng.")
    
    # Save the cleaned DataFrame to CSV & JSON
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", force_ascii=False, indent=2)
    print(f"   -> Đã lưu cleaned data vào: {settings.paths.clean_csv}")
    print(f"   -> Đã lưu cleaned data vào: {settings.paths.clean_json}")

    # 3. Build Test Set
    print("\n[*] Đang tạo bộ dữ liệu đánh giá (Test Set)...")
    test_set = build_test_set(df, settings.paths.eval_testset)
    
    print(f"   -> Đã tạo {len(test_set)} câu hỏi test.")
    print(f"   -> Đã lưu test set vào: {settings.paths.eval_testset}")
    
    print("\n[*] HOÀN THÀNH!")

if __name__ == "__main__":
    main()
