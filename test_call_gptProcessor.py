# 📁 test_call_gptProcessor.py

import os
from extractor.dataProcessor_gpt import CalendarDataProcessor

# ⛔ 클래스 정의 안 함, 그냥 인스턴스 생성 + 실행만 함

if __name__ == '__main__':
    print("✅ 직접 실행됨")

    test_file_path = os.path.join("ex_uploads", "texttest.txt")

    processor = CalendarDataProcessor()
    df = processor.process(test_file_path)

    if df.empty:
        print("❌ 일정 추출 실패 또는 결과 없음")
    else:
        print("\n📊 추출된 일정:")
        print(df.to_string(index=False))
