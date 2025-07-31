import os
import json
import pandas as pd
from dotenv import load_dotenv
from docx import Document
import fitz  # PyMuPDF
import easyocr
from datetime import datetime, timedelta
from openai import OpenAI  # ✅ 최신 SDK 방식

# 환경 변수 로드
load_dotenv()


class CalendarDataProcessor:
    def __init__(self):
        """
        OpenAI GPT 설정 및 OCR 초기화
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ 최신 방식
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.ocr_reader = easyocr.Reader(['ko', 'en'])

    def _extract_text(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        print(f"[DEBUG] 확장자: {ext}")

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

        print(f"[DEBUG] 텍스트 길이: {len(text)}")
        print(f"[DEBUG] 텍스트 미리보기:\n{text[:200]}")
        return text


    def _ask_ai(self, extracted_text: str) -> pd.DataFrame:
        """
        OpenAI GPT에게 텍스트를 넘기고 일정 정보를 DataFrame 형태로 받기
        """
        print(f"\n📤 [GPT로 보낸 프롬프트 내용 미리보기]:\n{prompt[:500]}")
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = (
            f"다음 문서에서 일정 관련 내용을 추출하여 아래 형식의 pandas DataFrame으로 정리하세요.\n\n"
            f" 규칙:\n"
            f"1. '오늘', '내일', '다음 주' 등 상대적 시간 표현은 ~부터', '~까지' 등의 표현dl 없다면 반드시 오늘 날짜 {today} 기준으로 YYYY-MM-DD 형식으로 변환하세요.\n"
            f"2. '~부터', '~까지' 등의 표현은 start, end로 분리하세요.\n"
            f"3. '~예정', '~하자' 포함 문장은 event로 간주하세요.\n"
            f"4. start와 end는 동일해도 허용됩니다.\n\n"
            
            f" 출력 형식은 반드시 아래처럼 DataFrame 생성 코드 한 줄만 출력하세요:\n"
            f"pd.DataFrame([\n"
            f"    {{'start': '{today}', 'end': '{tomorrow}', 'event': '길동이와 여행'}}\n"
            f"])\n\n"
            
            f"중요: 아래는 절대 출력하지 마세요:\n"
            f"- import pandas as pd\n"
            f"- df = ... 또는 변수 선언\n"
            f"- 설명, 주석\n\n"

            f"🔽 문서 내용:\n{extracted_text}"
        )


        try:
            response = self.client.chat.completions.create(  # ✅ 최신 방식
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "너는 문서에서 일정을 추출해주는 도우미야. pandas DataFrame 형식으로 알려줘."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            response_text = response.choices[0].message.content.strip()
            usage = response.usage
            print(f"\n📊 토큰 사용량: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")


            # GPT 응답 중에서 DataFrame 부분만 추출
            start_idx = response_text.find("pd.DataFrame([")
            end_idx = response_text.find("])", start_idx)

            if start_idx == -1 or end_idx == -1:
                raise ValueError("DataFrame 형식이 응답에 포함되지 않음.")

            json_like = response_text[start_idx + len("pd.DataFrame(["): end_idx].strip()
            json_str = "[" + json_like.rstrip(",") + "]"
            parsed = json.loads(json_str.replace("'", '"'))
            return pd.DataFrame(parsed)

        except Exception as e:
            print(f"❌ AI 처리 실패: {e}")
            print("🧾 전체 응답:\n", response_text if 'response_text' in locals() else "없음")
            return pd.DataFrame()

    def process(self, filepath: str) -> pd.DataFrame:
        """
        백엔드에서 사용할 전체 실행 파이프라인

        Args:
            filepath (str): 일정이 담긴 파일 경로

        Returns:
            pd.DataFrame: 추출된 일정 정보 DataFrame (start, end, event)
        """
        print(f"📂 파일 처리 시작: {filepath}")
        extracted_text = self._extract_text(filepath)

        if not extracted_text or "[❌" in extracted_text:
            print("🚫 지원되지 않는 파일이거나 텍스트 추출 실패")
            return pd.DataFrame()

        print("\n📄 추출된 텍스트 (일부):")
        print("--------------------------------------------------")
        print(extracted_text[:1000])
        print("--------------------------------------------------")

        df = self._ask_ai(extracted_text)

        if df.empty:
            print("🚫 일정 추출 실패 또는 결과 없음")
        else:
            print("\n📊 추출된 일정 DataFrame:")
            print(df)

        return df
    