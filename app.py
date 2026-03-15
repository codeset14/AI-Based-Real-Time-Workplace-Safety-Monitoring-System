from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os
import json
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

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

# Store detection results
detection_results = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/live")
def live():
    return render_template("live.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/results")
def results():
    return render_template("results.html", results=detection_results[::-1])

@app.route("/detect", methods=["POST"])
def detect():
    global consecutive_violations, alert_threshold, detection_results
    data = request.json.get("image")

    # Decode base64 image
    image_data = base64.b64decode(data.split(",")[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    results = model(frame, imgsz=416)

    annotated = results[0].plot()

    violation = False
    detected_objects = []

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        detected_objects.append(class_name)

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

    # Store result
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_name": f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
        "detected_objects": detected_objects,
        "status": "Unsafe" if violation else "Safe"
    }
    detection_results.append(result)

    # Encode image back to base64
    _, buffer = cv2.imencode(".jpg", annotated)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"image": encoded_image, "violation": should_alert, "consecutive": consecutive_violations})

@app.route("/upload_detect", methods=["POST"])
def upload_detect():
    global detection_results
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(ALERT_FOLDER, filename)
        file.save(file_path)

        # Read image
        frame = cv2.imread(file_path)
        results = model(frame, imgsz=416)
        annotated = results[0].plot()

        violation = False
        detected_objects = []

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            detected_objects.append(class_name)

            if class_name in ["NO-Hardhat", "NO-Safety Vest", "NO-Mask"]:
                violation = True

        if violation:
            cv2.putText(
                annotated,
                "SAFETY VIOLATION DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        # Save annotated image
        annotated_path = os.path.join(ALERT_FOLDER, f"annotated_{filename}")
        cv2.imwrite(annotated_path, annotated)

        # Store result
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_name": filename,
            "detected_objects": detected_objects,
            "status": "Unsafe" if violation else "Safe"
        }
        detection_results.append(result)

        return jsonify({"message": "Detection complete", "status": result["status"], "detected": detected_objects})

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