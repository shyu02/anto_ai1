import os
import json
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from docx import Document
import fitz  # PyMuPDF
import easyocr
from datetime import datetime, timedelta
# .env 파일 로드
load_dotenv()

class CalendarDataProcessor:
    def __init__(self):
        """
        Gemini API와 모델 설정, EasyOCR 초기화
        """
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash"))
        self.ocr_reader = easyocr.Reader(['ko', 'en'])  # 한글 + 영어 OCR 지원

    def _extract_text(self, filepath: str) -> str:
        """
        파일 확장자에 따라 텍스트 추출
        """
        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()

            elif ext == ".docx":
                doc = Document(filepath)
                text = "\n".join([p.text for p in doc.paragraphs])

            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(filepath)
                text = df.to_string(index=False)

            elif ext in [".jpg", ".jpeg", ".png"]:
                result = self.ocr_reader.readtext(filepath, detail=0)
                text = "\n".join(result)
            
            elif ext == ".pdf":
                with fitz.open(filepath) as pdf:
                    text = "".join([page.get_text() for page in pdf])
           
            else:
                return f"[❌ 지원하지 않는 파일 형식: {ext}]"

        except Exception as e:
            return f"[❌ 텍스트 추출 오류: {str(e)}]"
        
        return text
    def _ask_ai(self, extracted_text: str) -> pd.DataFrame:
        
            
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        """
        Gemini AI에게 일정 추출 요청 → pandas DataFrame으로 변환
        """
        prompt=( 
                    f"다음 문서에서 일정 관련 내용을 추출하여 아래 형식의 pandas DataFrame으로 정리하세요.\n\n"
                    f"📌 규칙:\n"
                    f"1. '오늘', '내일', '다음 주' 등 상대적 시간 표현은 반드시 오늘 날짜 {today}를 기준으로 YYYY-MM-DD 형식으로 변환하세요.\n"
                    f"2. '~부터', '~까지' 등의 기간 표현은 start와 end로 분리하여 날짜를 지정하세요.\n"
                    f"3. '~한다', '~하자', '~예정' 등의 표현이 포함된 문장은 event로 추출하세요.\n"
                    f"4. 시작일과 종료일이 동일하거나 하나만 있을 경우, start와 end에 동일한 날짜를 입력하세요.\n\n"
                    
                    f"📌 출력 형식:\n"
                    f"```python\n"
                    f"pd.DataFrame([\n"
                    f"    {{'start': '{today}', 'end': '{tomorrow}', 'event': '길동이와 여행'}}\n"
                    f"])"
                    f"\n```\n\n"
                    
                    f"📌 예시 문장:\n"
                    f"- 오늘부터 내일 길동이와 여행\n"
                    f"- 내일까지 길동이와 여행\n\n"
                    
                    f"🔽 문서 내용:\n{extracted_text}"
                )           
                

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            json_str = response_text.split("pd.DataFrame([", 1)[1].split("])")[0]
            json_str = "[" + json_str.strip().rstrip(",") + "]"
            parsed = json.loads(json_str.replace("'", '"'))
            return pd.DataFrame(parsed)

        except Exception as e:
            print(f"❌ AI 처리 실패: {e}")
            if 'response_text' in locals():
                print("🧾 AI 응답:\n", response_text)
            return pd.DataFrame()


    def process(self, filepath: str) -> pd.DataFrame:
        """
        전체 파이프라인 실행
        1. 텍스트 추출
        2. 중간 출력
        3. AI 처리
        4. DataFrame 반환
        """
        print(f"📂 파일 처리 시작: {filepath}")
        extracted_text = self._extract_text(filepath)

        print("\n📄 추출된 텍스트 내용:")
        print("--------------------------------------------------")
        print(extracted_text[:1000])  # 너무 길면 일부만 출력
        print("--------------------------------------------------")

        if "[❌" in extracted_text:
            print("🚫 지원되지 않는 파일이거나 추출 실패")
            return pd.DataFrame()

        df = self._ask_ai(extracted_text)

        print("\n📊 추출된 일정 DataFrame:")
        print(df)
        return df
