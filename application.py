from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from ultralytics import YOLO
import cv2
import numpy as np
import os
import json
import base64
import threading
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a random secret key

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
try:
    model = YOLO("best.pt")
    print("YOLO model loaded successfully.")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

# Folder for violation images (existing)
ALERT_FOLDER = "result"
os.makedirs(ALERT_FOLDER, exist_ok=True)

# Folder for video evidence frames (new)
RECORDING_FOLDER = "recording"
os.makedirs(RECORDING_FOLDER, exist_ok=True)

# Store detection results
detection_results = []

# In-memory video task store { task_id: { ...status... } }
video_tasks = {}


# ─────────────────────────────────────────────────────────────────
#  EXISTING ROUTES (unchanged)
# ─────────────────────────────────────────────────────────────────

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
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
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

    # Save every live annotated frame to results folder for browsing
    result_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    live_image_name = f"live_{result_timestamp}.jpg"
    cv2.imwrite(os.path.join(ALERT_FOLDER, live_image_name), annotated)

    # Store result (worker can be extended later using facial or metadata mapping)
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_name": live_image_name,
        "detected_objects": detected_objects,
        "status": "Unsafe" if violation else "Safe",
        "recording_images": [live_image_name],
        "worker": "Operator 1"
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
        annotated_filename = f"annotated_{filename}"
        annotated_path = os.path.join(ALERT_FOLDER, annotated_filename)
        cv2.imwrite(annotated_path, annotated)

        # Store result
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_name": annotated_filename,
            "detected_objects": detected_objects,
            "status": "Unsafe" if violation else "Safe",
            "recording_images": [annotated_filename],
            "worker": "Operator 1"
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


# ─────────────────────────────────────────────────────────────────
#  VIDEO DETECTION ROUTES (new)
# ─────────────────────────────────────────────────────────────────

@app.route("/trend_data")
def trend_data():
    """Return weekly violations and per-worker safety score stats."""

    today = datetime.now().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    daily_safe = {d: 0 for d in days}
    daily_unsafe = {d: 0 for d in days}
    worker_stats = {}

    for r in detection_results:
        try:
            dt = datetime.strptime(r.get('timestamp', ''), '%Y-%m-%d %H:%M:%S').date()
        except Exception:
            continue

        status = r.get('status', 'Safe')
        worker = r.get('worker', 'Unknown')

        if dt in daily_safe:
            if status == 'Safe':
                daily_safe[dt] += 1
            else:
                daily_unsafe[dt] += 1

        if worker not in worker_stats:
            worker_stats[worker] = {'safe': 0, 'unsafe': 0}

        if status == 'Safe':
            worker_stats[worker]['safe'] += 1
        else:
            worker_stats[worker]['unsafe'] += 1

    trend = [
        {'day': d.strftime('%a'), 'safe': daily_safe[d], 'unsafe': daily_unsafe[d]}
        for d in days
    ]

    scores = []
    for worker, counts in worker_stats.items():
        total = counts['safe'] + counts['unsafe']
        score = (counts['safe'] / total * 100) if total > 0 else 100
        scores.append({'worker': worker, 'safe': counts['safe'], 'unsafe': counts['unsafe'], 'score': round(score, 1)})

    return jsonify({'trend': trend, 'scores': scores})


@app.route("/video")
def video():
    return render_template("video.html")


@app.route("/recording/<path:filename>")
def serve_recording(filename):
    """Serve saved violation frame images from the recording folder."""
    return send_from_directory(RECORDING_FOLDER, filename)


@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve images from recording OR result directories."""
    recording_path = os.path.join(RECORDING_FOLDER, filename)
    result_path = os.path.join(ALERT_FOLDER, filename)
    if os.path.exists(recording_path):
        return send_from_directory(RECORDING_FOLDER, filename)
    elif os.path.exists(result_path):
        return send_from_directory(ALERT_FOLDER, filename)
    else:
        abort(404)


@app.route("/video_detect", methods=["POST"])
def video_detect():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
    """
    Accept an uploaded video, save it, spawn a background thread
    to run frame-by-frame YOLO detection, and return a task_id
    for the frontend to poll.
    """
    global detection_results

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename      = secure_filename(file.filename)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save the original upload into recording folder
    original_name = f"video_{timestamp_str}_{filename}"
    original_path = os.path.join(RECORDING_FOLDER, original_name)
    file.save(original_path)

    task_id = str(uuid.uuid4())

    # Initialise task entry before thread starts so /video_status
    # never returns 404 on an immediate poll
    video_tasks[task_id] = {
        "done":             False,
        "progress":         0,
        "stage":            "Queued…",
        "processed_frames": 0,
        "total_frames":     0,
        "violation_frames": 0,
        "violation_images": [],   # list of saved .jpg filenames
        "error":            None,
    }

    thread = threading.Thread(
        target=_process_video,
        args=(task_id, original_path, timestamp_str),
        daemon=True,
    )
    thread.start()

    return jsonify({"task_id": task_id})


@app.route("/video_status/<task_id>")
def video_status(task_id):
    """Frontend polls this every 1.5 s to get progress + results."""
    task = video_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Unknown task id"}), 404
    return jsonify(task)


# ─────────────────────────────────────────────────────────────────
#  Background worker
# ─────────────────────────────────────────────────────────────────

def _process_video(task_id, video_path, timestamp_str):
    if model is None:
        task = video_tasks[task_id]
        task["error"] = "Model not loaded"
        task["done"] = True
        return
    """
    Run YOLO on every frame.
    Save each violation frame as a .jpg into the recording folder.
    Update video_tasks[task_id] in-place so the poll endpoint
    reflects live progress.
    """
    task = video_tasks[task_id]

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            task["error"] = "Cannot open video file."
            task["done"]  = True
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 25

        task["total_frames"] = (total_frames // 41) + 1
        task["stage"]        = "Running YOLO detection…"

        frame_idx        = 0
        processed_count  = 0
        violation_count  = 0
        violation_images = []   # filenames only, served via /recording/<name>
        all_objects_seen = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % 41 != 0:
                frame_idx += 1
                continue

            results      = model(frame, imgsz=416, verbose=False)
            annotated    = results[0].plot()

            frame_violation  = False
            detected_objects = []

            for box in results[0].boxes:
                class_id   = int(box.cls[0])
                class_name = model.names[class_id]
                detected_objects.append(class_name)
                all_objects_seen.add(class_name)
                if class_name in ["NO-Hardhat", "NO-Safety Vest", "NO-Mask"]:
                    frame_violation = True

            if frame_violation:
                violation_count += 1

                # Stamp the frame
                cv2.putText(
                    annotated,
                    "SAFETY VIOLATION DETECTED",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    3,
                )

                # Build a human-readable video timestamp  mm:ss
                frame_time = frame_idx / fps
                mm = int(frame_time // 60)
                ss = int(frame_time % 60)
                time_label = f"{mm:02d}m{ss:02d}s"

                # Save violation frame as image
                img_name = f"violation_{timestamp_str}_frame{frame_idx:05d}_{time_label}.jpg"
                img_path = os.path.join(RECORDING_FOLDER, img_name)
                cv2.imwrite(img_path, annotated)

                violation_images.append({
                    "filename":        img_name,
                    "frame_number":    frame_idx,
                    "video_timestamp": f"{mm:02d}:{ss:02d}",
                    "detected_objects": list(set(detected_objects)),
                })

            processed_count += 1
            frame_idx += 1

            # Update progress every processed frame
            if processed_count % 1 == 0 or frame_idx >= total_frames:
                pct = int((processed_count / max(task["total_frames"], 1)) * 95)  # cap at 95 until done
                task["progress"]         = pct
                task["processed_frames"] = processed_count
                task["violation_frames"] = violation_count
                task["violation_images"] = violation_images

        cap.release()

        task["progress"]         = 100
        task["processed_frames"] = processed_count
        task["violation_frames"] = violation_count
        task["violation_images"] = violation_images
        task["stage"]            = "Complete!"
        task["done"]             = True

        # Append summary to the shared detection_results list
        # so it also shows up on the /results page
        detection_results.append({
            "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_name":      os.path.basename(video_path),
            "detected_objects": list(all_objects_seen),
            "status":          "Unsafe" if violation_count > 0 else "Safe",
            "recording_images": [img["filename"] for img in violation_images],
            "worker":          "Operator 1"
        })

    except Exception as e:
        task["error"] = str(e)
        task["done"]  = True


if __name__ == "__main__":
    try:
        print("Starting Flask app...")
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"Error starting app: {e}")