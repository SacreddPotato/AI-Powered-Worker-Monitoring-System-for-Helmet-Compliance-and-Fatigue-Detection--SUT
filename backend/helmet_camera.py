import cv2
import os
from ultralytics import YOLO

class HelmetCamera:
    def __init__(self, source=0):
        """
        Initialize Helmet Detection Camera
        Args:
            source: Video source (0 for webcam, or file path for video)
        """
        self.video = cv2.VideoCapture(source)
        
        # Load helmet detection model
        base_dir = os.path.dirname(os.path.abspath(__file__))
        helmet_model_path = os.path.join(base_dir, "best.pt")
        
        self.helmet_model = None
        if os.path.exists(helmet_model_path):
            self.helmet_model = YOLO(helmet_model_path)
            print(f"[INFO] Helmet model loaded from {helmet_model_path}")
        else:
            print(f"[WARNING] Helmet model not found at {helmet_model_path}")
        
        # Load standard YOLOv8 model for Person Detection
        try:
            self.person_model = YOLO('yolov8n.pt')
            print("[INFO] Person detection model (yolov8n.pt) loaded.")
        except Exception as e:
            print(f"[WARNING] Could not load yolov8n.pt: {e}")
            self.person_model = None
    
    def __del__(self):
        """Release video capture on deletion"""
        self.video.release()
    
    def get_frame(self):
        """
        Process a single frame with helmet detection
        Returns:
            bytes: JPEG encoded frame
        """
        success, frame = self.video.read()
        if not success:
            return None
        
        # Lists to store detection coordinates
        helmet_boxes = []

        # 1. Detect Helmets (Custom YOLO)
        if self.helmet_model is not None:
            # Run YOLO inference
            results = self.helmet_model(frame, conf=0.5, verbose=False)
            
            # Draw Helmets (Green)
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                helmet_boxes.append((x1, y1, x2, y2))
                
                # Draw Green Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Helmet {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 2. Detect People (Standard YOLOv8)
        # We use this to find workers who are NOT wearing helmets
        if self.person_model is not None:
            # Detect only class 0 (person)
            results_person = self.person_model(frame, classes=[0], conf=0.5, verbose=False)
            
            for box in results_person[0].boxes:
                px1, py1, px2, py2 = map(int, box.xyxy[0])
                
                # Check if this person has a corresponding helmet
                has_helmet = False
                
                for (hx1, hy1, hx2, hy2) in helmet_boxes:
                    # Logic: Check for intersection or close proximity
                    
                    # 1. Calculate intersection rectangle
                    ix1 = max(px1, hx1)
                    iy1 = max(py1, hy1)
                    ix2 = min(px2, hx2)
                    iy2 = min(py2, hy2)
                    
                    intersection_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                    
                    # If there is significant overlap (helmet is on the person)
                    if intersection_area > 0:
                        has_helmet = True
                        break
                    
                    # 2. Alternative Logic: Check if helmet is "floating" just above the person
                    # (Sometimes the person box cuts off at the forehead, but helmet sits higher)
                    h_center_x = (hx1 + hx2) // 2
                    h_bottom_y = hy2
                    
                    # If helmet is horizontally aligned with person
                    if px1 < h_center_x < px2:
                        # And helmet is near the top of the person box (within 20% of person height)
                        person_height = py2 - py1
                        if abs(h_bottom_y - py1) < (person_height * 0.2): 
                            has_helmet = True
                            break

                if not has_helmet:
                    # Draw Red Box for No Helmet
                    cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 2)
                    cv2.putText(frame, "HELMET NOT FOUND", (px1, py1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            return jpeg.tobytes()
        return None
