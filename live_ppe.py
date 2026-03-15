from ultralytics import YOLO
import cv2
import os
import json
from datetime import datetime

# Load trained model
model = YOLO("best.pt")

# Load alert threshold from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        alert_threshold = config.get("alert_threshold", 1)
except FileNotFoundError:
    alert_threshold = 3

# Consecutive violation counter
consecutive_violations = 0

# Create output folder if not exists
output_folder = "result"
os.makedirs(output_folder, exist_ok=True)

# Open video file
cap = cv2.VideoCapture("WhatsApp Video 2026-03-15 at 5.59.29 PM.mp4")  # Replace with actual path

print(f"Starting Workplace Safety Monitoring... (Alert Threshold: {alert_threshold} frames)")

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop back to start
        continue

    results = model(frame)

    annotated_frame = results[0].plot()

    violation_detected = False

    # Check for safety violations
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]

        if class_name in ["NO-Hardhat", "NO-Safety Vest", "NO-Mask"]:
            violation_detected = True

    # Track consecutive violations and apply threshold before alerting
    if violation_detected:
        consecutive_violations += 1
    else:
        consecutive_violations = 0

    if consecutive_violations >= alert_threshold:
        cv2.putText(
            annotated_frame,
            "SAFETY VIOLATION DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        # Save frame with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(output_folder, f"violation_{timestamp}.jpg")
        cv2.imwrite(save_path, annotated_frame)

    # Show consecutive count on frame
    cv2.putText(
        annotated_frame,
        f"Consecutive: {consecutive_violations} / Threshold: {alert_threshold}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.imshow("Workplace Safety Monitoring", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()