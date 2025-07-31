from extractor.dataProcessor import CalendarDataProcessor

# 테스트할 파일 경로
filepath = "ex_uploads/testtext.txt"

# 인스턴스 생성
processor = CalendarDataProcessor()

# 처리 실행
df = processor.process(filepath)

# 결과 출력
print("\n🎯 최종 일정 DataFrame:")
print(df)