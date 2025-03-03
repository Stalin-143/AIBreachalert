import os
import re
import threading
import time
import functools
import pickle
import numpy as np
from queue import Queue
from flask import Flask, request, jsonify, render_template
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)

# Settings
THREADS = 10
MAX_FILE_SIZE_MB = 50  # Skip files larger than 50MB
DATA_DIR = "data"
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 5

# Load Random Forest model and TF-IDF vectorizer
with open("random_forest.pkl", "rb") as f:
    rf_model = pickle.load(f)
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

def rate_limiter(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        if ip not in RATE_LIMIT:
            RATE_LIMIT[ip] = []
        RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if current_time - t < RATE_LIMIT_WINDOW]
        if len(RATE_LIMIT[ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return jsonify({"status": "error", "message": "Too many requests. Try again later."}), 429
        RATE_LIMIT[ip].append(current_time)
        return func(*args, **kwargs)
    return wrapper

def scan_file(file_path, email):
    """Scans a single file for the email."""
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_MB * 1024 * 1024:
            return False
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                if re.search(rf"\b{re.escape(email)}\b", line, re.IGNORECASE):
                    return True
    except Exception:
        pass
    return False

def worker(email, files_to_scan, result_queue, lock):
    while not files_to_scan.empty():
        file_path = files_to_scan.get()
        if scan_file(file_path, email):
            with lock:
                result_queue.put(True)

def check_breach(email):
    email = email.strip().lower()
    result_queue = Queue()
    lock = threading.Lock()

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return {"status": "error", "message": f"Data directory '{DATA_DIR}' was missing and created."}

    files_to_scan = Queue()
    for root, _, files in os.walk(DATA_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.getsize(file_path) <= MAX_FILE_SIZE_MB * 1024 * 1024:
                files_to_scan.put(file_path)

    threads = []
    for _ in range(min(THREADS, files_to_scan.qsize())):
        t = threading.Thread(target=worker, args=(email, files_to_scan, result_queue, lock))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    found_any = not result_queue.empty()
    if found_any:
        return {"status": "breached", "message": "⚠️ Your email was found in a data breach! Change your password!"}
    
    # AI-Based Classification using RandomForest
    email_vectorized = vectorizer.transform([email])
    rf_prediction = rf_model.predict(email_vectorized)[0]

    if rf_prediction == 1:
        return {"status": "potential breach", "message": "⚠️ Your email has a high risk of being breached!"}
    
    return {"status": "safe", "message": "✅ No breach found."}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/breach")
def breach():
    return render_template("breach.html")

@app.route("/check", methods=["POST"])
@rate_limiter
def check():
    email = request.form.get("email")
    if not email:
        return jsonify({"status": "error", "message": "Please provide an email."})

    result = check_breach(email)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
