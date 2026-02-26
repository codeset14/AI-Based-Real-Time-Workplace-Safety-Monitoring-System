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

👷 Person

When a violation is detected:

⚠ Real-time alert is displayed

📦 Bounding boxes highlight non-compliant workers

📸 Violation frames are saved for audit purposes

The system is deployed using Streamlit, providing a clean and interactive monitoring interface.

🧠 Tech Stack

YOLOv8 (Ultralytics) – Object Detection

PyTorch – Deep Learning Framework

OpenCV – Real-Time Video Processing

Streamlit – Interactive Web Dashboard

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
├── app.py
└── README.md
🔮 Future Enhancements

SMS/Email alerts for violations

Cloud-based CCTV integration

Analytics dashboard with violation statistics

Multi-camera support

Edge device deployment

