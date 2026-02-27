from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os
import base64
from datetime import datetime

app = Flask(__name__)

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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(ALERT_FOLDER, f"violation_{timestamp}.jpg")
        cv2.imwrite(file_path, annotated)

    # Encode image back to base64
    _, buffer = cv2.imencode(".jpg", annotated)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"image": encoded_image, "violation": violation})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)