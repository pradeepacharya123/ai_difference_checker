import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# load .env
load_dotenv()

from backend.services.pdf_service import extract_text_from_file
from backend.services.diff_service import compute_diff_and_stats
from backend.services.ai_service import get_hf_summary
from backend.utils.file_handler import save_uploaded_file



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# allow frontend dev server
CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": "*"}}
)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/upload", methods=["POST"])
def upload():
    """
    Accept two files: 'file_a' and 'file_b'.
    Returns:
      - html_diff: HTML table (difflib.HtmlDiff)
      - total_changes, add_pct, del_pct
      - diff_text: plain text diff (useful to send to /api/summary)
    """
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")

    if not file_a or not file_b:
        return jsonify({"error": "Both files (file_a, file_b) are required."}), 400

    # Save files with unique names
    saved_a = save_uploaded_file(file_a, app.config["UPLOAD_FOLDER"], prefix="A_")
    saved_b = save_uploaded_file(file_b, app.config["UPLOAD_FOLDER"], prefix="B_")

    # Extract text (works for .txt and .pdf)
    text_a = extract_text_from_file(saved_a)
    text_b = extract_text_from_file(saved_b)

    # Compute diff, stats, html diff and text diff
    results = compute_diff_and_stats(text_a, text_b)

    # Return JSON (diff_text can be large - frontend may choose to request summary separately)
    return jsonify({
        "html_diff": results["html_diff"],   # HTML string (table)
        "total_changes": results["total"],
        "add_pct": results["add_pct"],
        "del_pct": results["del_pct"],
        "diff_text": results["diff_text"]    # raw diff lines (ndiff)
    }), 200

@app.route("/api/summary", methods=["POST"])
def summary():
    """
    Accepts JSON: { "diff_text": "..." }
    Calls Hugging Face Inference API and returns the summary.
    """
    body = request.get_json(force=True, silent=True)
    if not body or "diff_text" not in body:
        return jsonify({"error": "JSON body with 'diff_text' required."}), 400

    diff_text = body["diff_text"] or ""
    # to avoid extremely large payloads, truncate if necessary (you can adjust limit)
    MAX_CHARS = 30000
    truncated = diff_text[:MAX_CHARS]

    # get_hf_summary uses HF_API_KEY & HF_API_URL from env
    summary = get_hf_summary(truncated)

    return jsonify({"summary": summary}), 200

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=5000, debug=True)
