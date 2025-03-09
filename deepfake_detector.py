import os
import cv2
import torch
from transformers import pipeline
from PIL import Image

# Ensure OpenCV works in a headless environment
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

# Check for GPU availability
device = 0 if torch.cuda.is_available() else -1

# Load deepfake detection model
deepfake_model = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-Model", device=device)

def analyse_video(video_path):
    cap = cv2.VideoCapture(video_path)
    try:
        ret, frame = cap.read()
        if not ret:
            raise ValueError("⚠️ Unable to read video frame. The file might be corrupt.")
        
        # Convert frame to PIL image
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Run deepfake detection
        result = deepfake_model(pil_image)

        # Ensure results exist
        if not result or len(result) == 0:
            return "⚠️ No prediction could be made."

        return f"Deepfake Detection: {result[0]['label']} ({result[0]['score']:.2%} confidence)"

    finally:
        cap.release()
