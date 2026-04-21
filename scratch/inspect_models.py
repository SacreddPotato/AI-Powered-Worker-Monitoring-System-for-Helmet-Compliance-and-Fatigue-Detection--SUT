import sys
import os
from ultralytics import YOLO

models_dir = r"c:\Users\o3995\Downloads\Website-Safe-Vision-AI-2(2)\backend\ml_models"
model_files = [
    "face_shield_detection.pt",
    "safety_suit_detection.pt",
    "goggles_detection.pt",
    "vest_detection.pt"
]

for filename in model_files:
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    try:
        model = YOLO(path)
        print(f"\nModel: {filename}")
        print(f"Classes: {model.names}")
    except Exception as e:
        print(f"Error loading {filename}: {e}")
