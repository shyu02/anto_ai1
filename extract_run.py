#백엔드 에서 dataProcessor 사용
from flask import Flask, request, jsonify
import os
from extractor.dataProcessor import CalendarDataProcessor  # 우리가 만든 클래스

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "파일이 없습니다."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "파일 이름이 비어 있습니다."}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        processor = CalendarDataProcessor()
        df = processor.process(filepath)

        if df.empty:
            return jsonify({"success": False, "message": "일정 추출 실패"}), 200

        # DataFrame을 JSON으로 변환해서 응답
        return jsonify({
            "success": True,
            "data": df.to_dict(orient="records")
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)