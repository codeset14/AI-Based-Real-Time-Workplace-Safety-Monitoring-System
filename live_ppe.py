from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load trained model
model = YOLO("best.pt")

# Create workplace folder if not exists
output_folder = "result"
os.makedirs(output_folder, exist_ok=True)

# Open webcam
cap = cv2.VideoCapture(0)

print("Starting Workplace Safety Monitoring...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    violation_detected = False

    # Check for safety violations
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]

        if class_name in ["NO-Hardhat", "NO-Safety Vest", "NO-Mask"]:
            violation_detected = True

    # If violation detected
    if violation_detected:
        cv2.putText(
            annotated_frame,
            "⚠ SAFETY VIOLATION DETECTED",
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

    cv2.imshow("Workplace Safety Monitoring", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
