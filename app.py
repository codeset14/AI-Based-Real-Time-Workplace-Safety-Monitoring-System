from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os
import json
import base64
from datetime import datetime

app = Flask(__name__)

# Load config from file
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"alert_threshold": 1}  # Default

# Save config to file
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)

# Global config and counter
config = load_config()
alert_threshold = config.get("alert_threshold", 1)
consecutive_violations = 0  # Tracks consecutive violation frames
# Load YOLO model once
model = YOLO("best.pt")

# Folder for violation images
ALERT_FOLDER = "result"
os.makedirs(ALERT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    global consecutive_violations, alert_threshold
    data = request.json.get("image")

    # Decode base64 image
    image_data = base64.b64decode(data.split(",")[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    results = model(frame, imgsz=416)

    annotated = results[0].plot()

    violation = False

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]

        if class_name in ["NO-Hardhat", "NO-Safety Vest", "NO-Mask"]:
            violation = True

    # Update consecutive counter
    if violation:
        consecutive_violations += 1
    else:
        consecutive_violations = 0

    # Only alert if threshold reached
    should_alert = consecutive_violations >= alert_threshold

    if should_alert:
        cv2.putText(
            annotated,
            "SAFETY VIOLATION DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(ALERT_FOLDER, f"violation_{timestamp}.jpg")
        cv2.imwrite(file_path, annotated)

    # Encode image back to base64
    _, buffer = cv2.imencode(".jpg", annotated)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"image": encoded_image, "violation": should_alert, "consecutive": consecutive_violations})

@app.route("/settings", methods=["GET", "POST"])
def settings():
    global alert_threshold, config
    if request.method == "POST":
        try:
            new_threshold = int(request.json.get("alert_threshold"))
            if not (1 <= new_threshold <= 10):
                return jsonify({"error": "Threshold must be between 1 and 10"}), 400
            config["alert_threshold"] = new_threshold
            alert_threshold = new_threshold
            save_config(config)
            return jsonify({"message": "Threshold updated successfully"})
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid input: must be a number"}), 400
    else:
        return jsonify({"alert_threshold": alert_threshold})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)