import os
from extractor.dataProcessor_gpt import CalendarDataProcessor

if __name__ == '__main__':
    print("✅ 직접 실행됨")
    
    print("[📂 현재 ex_uploads 폴더 안 파일들]:")
    print(os.listdir(os.path.join(os.path.dirname(__file__), "ex_uploads")))
    
    # ✅ 현재 파일 위치 기준으로 절대 경로 구성
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(base_dir, "ex_uploads", "testtext.txt")

    processor = CalendarDataProcessor()
    df = processor.process(test_file_path)

    if df.empty:
        print("❌ 일정 추출 실패 또는 결과 없음")
    else:
        print("\n📊 추출된 일정:")
        print(df.to_string(index=False))
