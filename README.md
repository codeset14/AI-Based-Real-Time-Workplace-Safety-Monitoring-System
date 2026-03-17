🚧 AI-Based Real-Time Workplace Safety Monitoring System

🏆 Hackathon Project | 🧠 Computer Vision | ⚡ Real-Time AI Monitoring

📌 Overview

Workplace environments such as construction sites and industrial plants are high-risk zones where strict adherence to Personal Protective Equipment (PPE) is critical. Manual monitoring of safety compliance is inefficient, inconsistent, and difficult to scale across large worksites.

This project presents an AI-powered real-time safety monitoring system that automatically detects PPE compliance using deep learning and computer vision. The system identifies safety violations instantly and generates alerts, helping reduce workplace accidents through intelligent automation.

🚨 Problem Statement

Industrial environments face frequent safety violations due to:

Inconsistent PPE usage (helmets, vests, masks)

Lack of continuous monitoring

Human supervision limitations

Delayed identification of safety risks

Manual inspection cannot provide 24/7 monitoring across multiple zones, leading to increased accident risk and regulatory non-compliance.

💡 Proposed Solution

This system leverages YOLOv8 object detection to monitor PPE compliance in real time via webcam or CCTV feed.

The trained model detects:

🟢 Hardhat

🟢 Safety Vest

🟢 Mask

🔴 NO-Hardhat

🔴 NO-Safety Vest

🔴 NO-Mask

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AI-Based-Real-Time-Workplace-Safety-Monitoring-System
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python application.py
   ```

4. Open your browser and go to `http://localhost:5000`

## Features

- Live real-time PPE detection via webcam with violation highlighting
- Live detection includes 2-second repeating beep on safety violation, auto-stop on camera stop
- Image upload analysis with safe/unsafe classification and annotated evidence image saving
- Video upload analysis with background processing, progress status, and evidence frame capture
- Results tab with searchable report table including timestamps, status, and detected objects
- Clicking on a result opens modal with stored images (recording/result folder) and keyboard arrow navigation (←/→/Esc)
- New trend dashboard in Video tab showing weekly violations and per-worker safety score charts (Chart.js)
- REST endpoint `/trend_data` for live-updating chart data from in-memory detection results
- Per-worker safety score computation + weekly safe/unsafe trend updates every 5 seconds
- Auto-serving images from `recording/` and `result/` via `/recording/<filename>` and `/images/<filename>` endpoints


## Usage

- **Live Detection**: Start real-time monitoring
- **Upload Image**: Analyze static images
- **Video Analysis**: Process video files for violations
- **Results**: View historical data

## Technologies Used

- Flask (Web Framework)
- YOLOv8 (Object Detection)
- OpenCV (Computer Vision)
- HTML/CSS/JavaScript (Frontend)

📸 Violation frames are saved for audit purposes

The system is deployed using Streamlit, providing a clean and interactive monitoring interface.

🧠 Tech Stack

YOLOv8 (Ultralytics) – Object Detection

PyTorch – Deep Learning Framework

OpenCV – Real-Time Video Processing

HTML/CSS/JavaScript – Interactive Web Dashboard

Python – Backend Implementation

🎯 Hackathon Impact

This project demonstrates:

Real-time AI-based safety enforcement

Scalable industrial monitoring solution

Automated violation detection and logging

Practical deployment-ready MVP

It showcases how AI can move beyond research and deliver tangible safety improvements in real-world industrial environments.

🚀 Key Features

✔ Live camera PPE detection
✔ Safety violation alert system
✔ Automatic evidence capture
✔ Lightweight and fast inference
✔ Easy deployment and scalability

📂 Project Structure
HackNova/
│
├── css-data/
├── workplace/
├── best.pt
├── live_ppe.py
├── application.py
└── README.md
🔮 Future Enhancements

SMS/Email alerts for violations

Cloud-based CCTV integration

Analytics dashboard with violation statistics

Multi-camera support

Edge device deployment

