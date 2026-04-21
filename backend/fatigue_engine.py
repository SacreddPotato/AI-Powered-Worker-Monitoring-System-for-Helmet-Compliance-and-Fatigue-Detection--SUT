from typing import Dict

import cv2
import dlib
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
from imutils import face_utils
from PIL import Image
from scipy.spatial import distance as dist
from torchvision import transforms


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


class FatigueHybridEngine:
    def __init__(
        self,
        model_path: str,
        shape_predictor_path: str,
        head_tilt_alert_degrees: float = 15.0,
        fatigue_threshold: float = 0.55,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.head_tilt_alert_degrees = float(head_tilt_alert_degrees)
        self.fatigue_threshold = float(fatigue_threshold)
        self.ear_threshold = 0.28
        self.mar_scale_max = 1.0
        # Tuned for observed closed-eye EAR band (~0.18-0.22).
        self.ear_force_fatigue_threshold = 0.22
        self.mar_narrow_threshold = 0.28

        self.model = models.swin_v2_s(weights=None)
        self.model.head = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(in_features=768, out_features=1, bias=True),
        )

        state = torch.load(model_path, map_location=self.device)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        self.model.load_state_dict(state, strict=False)
        self.model.to(self.device)
        self.model.eval()

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(shape_predictor_path)
        (self.left_start, self.left_end) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.right_start, self.right_end) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        self.mouth_start, self.mouth_end = (60, 68)

        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

        self.model_points_3d = np.array(
            [
                (0.0, 0.0, 0.0),
                (0.0, -63.6, -12.5),
                (-43.3, 32.7, -26.0),
                (43.3, 32.7, -26.0),
                (-28.9, -28.9, -24.1),
                (28.9, -28.9, -24.1),
            ],
            dtype=np.float64,
        )

    def _eye_aspect_ratio(self, eye) -> float:
        a = dist.euclidean(eye[1], eye[5])
        b = dist.euclidean(eye[2], eye[4])
        c = dist.euclidean(eye[0], eye[3])
        if c == 0:
            return 0.0
        return float((a + b) / (2.0 * c))

    def _mouth_aspect_ratio(self, mouth) -> float:
        a = dist.euclidean(mouth[1], mouth[7])
        b = dist.euclidean(mouth[2], mouth[6])
        c = dist.euclidean(mouth[3], mouth[5])
        d = dist.euclidean(mouth[0], mouth[4])
        if d == 0:
            return 0.0
        return float((a + b + c) / (3.0 * d))

    def _head_pose(self, landmarks, frame_h, frame_w):
        image_points = np.array(
            [
                landmarks[30],
                landmarks[8],
                landmarks[36],
                landmarks[45],
                landmarks[48],
                landmarks[54],
            ],
            dtype="double",
        )
        focal_length = frame_w / (2 * np.tan(np.radians(30)))
        center = (frame_w / 2, frame_h / 2)
        camera_matrix = np.array(
            [
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1],
            ],
            dtype="double",
        )
        dist_coeffs = np.zeros((4, 1))
        success, rotation_vector, _ = cv2.solvePnP(
            self.model_points_3d,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            nose = (int(image_points[0][0]), int(image_points[0][1]))
            return 0.0, 0.0, 0.0, nose, nose

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)
        pitch = float(angles[0])
        yaw = float(angles[1])
        roll = float(angles[2])
        nose = (int(image_points[0][0]), int(image_points[0][1]))
        line_dx = float(yaw * 2.0)
        line_dy = float(-pitch * 2.0)
        line_end = (int(nose[0] + line_dx), int(nose[1] + line_dy))
        # Keep overlay direction stable (nose -> forehead); tilt thresholding uses abs values separately.
        if line_end[1] > nose[1]:
            line_end = (int(nose[0] - line_dx), int(nose[1] - line_dy))
        return pitch, yaw, roll, nose, line_end

    def _fatigue_ml_probability(self, frame, rect) -> float:
        x, y, w, h = face_utils.rect_to_bb(rect)
        frame_h, frame_w = frame.shape[:2]
        pad = 12
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame_w, x + w + pad)
        y2 = min(frame_h, y + h + pad)
        face = frame[y1:y2, x1:x2]
        if face.size == 0:
            return 0.0

        face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(face_rgb)
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(tensor)
            prob = torch.sigmoid(output).item()
        return float(prob)

    def analyze(self, frame) -> Dict:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if len(rects) == 0:
            return {
                "status": "no_face",
                "fatigue_probability": 0.0,
                "ear": 0.0,
                "mar": 0.0,
                "head_tilt_degrees": 0.0,
                "hybrid_score": 0.0,
                "is_fatigued": False,
                "head_tilt_exceeded": False,
                "facial_plotting_used": False,
                "landmarks_count": 0,
                "face_box": None,
                "landmarks": [],
                "pose_line": None,
            }

        rect = rects[0]
        x, y, w, h = face_utils.rect_to_bb(rect)
        shape = self.predictor(gray, rect)
        landmarks = face_utils.shape_to_np(shape)

        left_ear = self._eye_aspect_ratio(landmarks[self.left_start : self.left_end])
        right_ear = self._eye_aspect_ratio(landmarks[self.right_start : self.right_end])
        ear = (left_ear + right_ear) / 2.0

        mouth = landmarks[self.mouth_start : self.mouth_end]
        mar = self._mouth_aspect_ratio(mouth)

        frame_h, frame_w = frame.shape[:2]
        pitch, yaw, roll, nose, line_end = self._head_pose(landmarks, frame_h, frame_w)
        head_tilt_degrees = max(abs(pitch), abs(roll))
        head_tilt_exceeded = head_tilt_degrees > self.head_tilt_alert_degrees

        ml_prob = self._fatigue_ml_probability(frame, rect)
        ear_score = _clamp((self.ear_threshold - ear) / self.ear_threshold, 0.0, 1.0)
        # Mouth openness is a continuous supporting signal (no hard yawning threshold).
        mar_score = _clamp(mar / self.mar_scale_max, 0.0, 1.0)
        hybrid_score = (0.65 * ml_prob) + (0.3 * ear_score) + (0.05 * mar_score)
        eyes_closed_hard = ear <= self.ear_force_fatigue_threshold
        mar_too_narrow = mar <= self.mar_narrow_threshold
        forced_fatigue_state = bool(
            eyes_closed_hard or (mar_too_narrow and ear <= (self.ear_threshold * 0.95))
        )
        if forced_fatigue_state:
            hybrid_score = max(hybrid_score, self.fatigue_threshold + 0.05)
        is_fatigued = forced_fatigue_state or (hybrid_score >= self.fatigue_threshold)

        return {
            "status": "ok",
            "fatigue_probability": round(ml_prob, 4),
            "ear": round(float(ear), 4),
            "mar": round(float(mar), 4),
            "head_tilt_degrees": round(float(head_tilt_degrees), 2),
            "head_pitch": round(float(pitch), 2),
            "head_yaw": round(float(yaw), 2),
            "head_roll": round(float(roll), 2),
            "ear_score": round(float(ear_score), 4),
            "mar_score": round(float(mar_score), 4),
            "hybrid_score": round(float(hybrid_score), 4),
            "is_fatigued": bool(is_fatigued),
            "forced_fatigue_state": bool(forced_fatigue_state),
            "eyes_closed_hard": bool(eyes_closed_hard),
            "mar_too_narrow": bool(mar_too_narrow),
            "ear_force_fatigue_threshold": float(self.ear_force_fatigue_threshold),
            "mar_narrow_threshold": float(self.mar_narrow_threshold),
            "head_tilt_exceeded": bool(head_tilt_exceeded),
            "facial_plotting_used": True,
            "landmarks_count": int(len(landmarks)),
            "face_box": {
                "x1": int(x),
                "y1": int(y),
                "x2": int(x + w),
                "y2": int(y + h),
            },
            "landmarks": [[int(px), int(py)] for (px, py) in landmarks.tolist()],
            "pose_line": {
                "start": [int(nose[0]), int(nose[1])],
                "end": [int(line_end[0]), int(line_end[1])],
            },
        }
