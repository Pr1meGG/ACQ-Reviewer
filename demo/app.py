from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def summarize(pylint_out, flake8_out):
    return {
        "issues": pylint_out.count(":"),
        "style_issues": flake8_out.count(":"),
        "quality_score": max(100 - (pylint_out.count(":") * 5), 40),
        "verdict": "Needs Improvement" if pylint_out else "Good Quality"
    }


if __name__ == "__main__":
    app.run(debug=True)
