import os
import cv2
import torch
from transformers import pipeline
from PIL import Image

# Load deepfake detection model
deepfake_model = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-Model")

def analyse_video(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Unable to read video frame")
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    result = deepfake_model(pil_image)
    cap.release()
    return f"Deepfake Detection: {result[0]['label']}"

