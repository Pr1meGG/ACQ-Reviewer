import subprocess
import tempfile
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_tool(command, file_path):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def analyze_code(code):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
        temp.write(code.encode())
        file_path = temp.name

    pylint_out = run_tool(
        ["pylint", file_path, "--disable=all", "--enable=unused-import,missing-docstring"],
        file_path
    )

    flake8_out = run_tool(
        ["flake8", file_path],
        file_path
    )

    issues = pylint_out.count(":") + flake8_out.count(":")
    score = max(100 - issues * 10, 40)

    verdict = "Good Quality" if score >= 80 else "Needs Improvement"

    os.unlink(file_path)

    return {
        "summary": {
            "quality_score": score,
            "total_issues": issues,
            "verdict": verdict
        },
        "details": {
            "pylint": pylint_out.strip(),
            "flake8": flake8_out.strip()
        }
    }

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    report = analyze_code(code)
    return jsonify(report)

@app.route("/health")
def health():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
