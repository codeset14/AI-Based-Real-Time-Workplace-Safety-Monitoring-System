import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av
import cv2
import os
from datetime import datetime
from ultralytics import YOLO

st.set_page_config(page_title="AI Workplace Safety Monitor", layout="wide")
st.title("🚧 AI-Based Real-Time Workplace Safety Monitoring")

@st.cache_resource
def load_model():
    return YOLO("best.pt")

model = load_model()

ALERT_FOLDER = "workplace"
os.makedirs(ALERT_FOLDER, exist_ok=True)

st.sidebar.title("Controls")
camera_on = st.sidebar.toggle("Turn Camera On/Off")

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        results = model(img)
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
                "⚠ SAFETY VIOLATION DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(ALERT_FOLDER, f"violation_{timestamp}.jpg")
            cv2.imwrite(file_path, annotated)

        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

if camera_on:
    webrtc_streamer(
        key="ppe-monitor",
        video_processor_factory=VideoProcessor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
    )

st.subheader("🚨 Recent Safety Violations")

alert_images = sorted(
    [os.path.join(ALERT_FOLDER, f) for f in os.listdir(ALERT_FOLDER)],
    reverse=True
)

if alert_images:
    for img in alert_images[:5]:
        st.image(img, use_column_width=True)
else:
    st.info("No safety violations detected yet.")