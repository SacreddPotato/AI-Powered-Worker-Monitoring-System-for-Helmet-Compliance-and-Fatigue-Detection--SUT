import base64
import os
import re
import threading
from io import BytesIO
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

from config import (
    FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD,
    HEAD_TILT_ALERT_DEGREES,
)
fatigue_import_error = None
try:
    from fatigue_engine import FatigueHybridEngine
except Exception as fatigue_import_error:  # pragma: no cover
    FatigueHybridEngine = None

mediapipe_import_error = None
try:
    import mediapipe as mp
except Exception as mediapipe_import_error:  # pragma: no cover
    mp = None


_LEFT_EYE_LANDMARKS = [33, 133, 159, 145, 153, 144, 163, 7]
_RIGHT_EYE_LANDMARKS = [362, 263, 386, 374, 380, 381, 382, 398]
_FEATURE_MISSING_CONFIDENCE = 0.7
_PERSON_FALLBACK_MISSING_CONFIDENCE = 0.72
_FOOT_LANDMARK_VISIBILITY_THRESHOLD = 0.35
_FOOTWEAR_LABEL_HINTS = {
    "boot",
    "shoe",
    "sneaker",
    "loafer",
    "sandal",
    "slipper",
    "clog",
    "trainer",
    "footwear",
}


def decode_base64_image(image_base64: str):
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _iou(box_a, box_b) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0

    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))
    return inter_area / float(area_a + area_b - inter_area)


def _box_center_inside(inner_box, outer_box) -> bool:
    ix1, iy1, ix2, iy2 = inner_box
    ox1, oy1, ox2, oy2 = outer_box
    center_x = (ix1 + ix2) / 2.0
    center_y = (iy1 + iy2) / 2.0
    return ox1 <= center_x <= ox2 and oy1 <= center_y <= oy2


def _normalize_label(label: str) -> str:
    label = re.sub(r"[_\-]+", " ", str(label).lower())
    label = re.sub(r"\s+", " ", label).strip()
    return label


def _is_missing_label(label: str) -> bool:
    normalized = _normalize_label(label)
    return normalized.startswith("no ") or normalized.startswith("without ")


class PPEModelAdapter:
    def __init__(self, model_key: str, model_info: Dict):
        self.model_key = model_key
        self.display_name = model_info["display_name"]
        self.description = model_info["description"]
        self.weights_path = model_info["weights_path"]
        self.target_labels = {label.lower() for label in model_info.get("target_labels", [])}
        self.normalized_target_labels = {
            _normalize_label(label) for label in model_info.get("target_labels", [])
        }
        self.strict_target_match = bool(model_info.get("strict_target_match", True))
        self.supports_qr = model_key == "vest"
        self._absence_uses_features = model_key in {"gloves", "goggles", "boots"}
        self._absence_uses_person_overlap = model_key in {"vest", "faceshield", "safetysuit"}
        self.person_model_path = model_info.get("person_model_path")

        self.available = False
        self.load_error = None
        self._model = None
        self._person_model = None
        self._supports_explicit_missing_classes = False
        self._mp_hands = None
        self._mp_face_mesh = None
        self._mp_pose = None
        self._feature_lock = threading.Lock()
        self.model_classes = []
        self.matched_labels = []
        self._qr_detector = cv2.QRCodeDetector() if self.supports_qr else None
        self._load()

    def _load(self):
        if not os.path.exists(self.weights_path):
            self.load_error = (
                f"Weights missing at {self.weights_path}. "
                "Ensure model files are committed with Git LFS and run 'git lfs pull'."
            )
            return

        try:
            self._model = YOLO(self.weights_path)
            names = self._model.names or {}
            self.model_classes = sorted(
                {
                    _normalize_label(name)
                    for name in names.values()
                    if str(name).strip()
                }
            )
            if self.normalized_target_labels:
                self.matched_labels = sorted(
                    self.normalized_target_labels.intersection(self.model_classes)
                )
                if not self.matched_labels and self.strict_target_match:
                    preview_classes = ", ".join(self.model_classes[:12]) or "none"
                    self.available = False
                    self.load_error = (
                        "Configured target labels are not present in model classes. "
                        f"Targets={sorted(self.normalized_target_labels)}; model_classes={preview_classes}"
                    )
                    self._model = None
                    return
                if not self.matched_labels:
                    self.matched_labels = list(self.model_classes)
            else:
                self.matched_labels = list(self.model_classes)
            self._supports_explicit_missing_classes = any(
                _is_missing_label(label) for label in self.matched_labels
            )
            self.available = True

            if self._absence_uses_features:
                if mp is None:
                    self.load_error = (
                        f"{self.load_error}; " if self.load_error else ""
                    ) + f"MediaPipe unavailable: {mediapipe_import_error}"
                else:
                    if self.model_key == "gloves":
                        self._mp_hands = mp.solutions.hands.Hands(
                            static_image_mode=False,
                            max_num_hands=6,
                            min_detection_confidence=0.35,
                            min_tracking_confidence=0.35,
                        )
                    elif self.model_key == "goggles":
                        self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                            static_image_mode=False,
                            max_num_faces=6,
                            refine_landmarks=True,
                            min_detection_confidence=0.35,
                            min_tracking_confidence=0.35,
                        )
                    elif self.model_key == "boots":
                        self._mp_pose = mp.solutions.pose.Pose(
                            static_image_mode=False,
                            model_complexity=1,
                            min_detection_confidence=0.35,
                            min_tracking_confidence=0.35,
                        )

            if self._absence_uses_person_overlap:
                self._load_person_model_for_absence()
        except Exception as exc:
            self.available = False
            self.load_error = str(exc)

    @staticmethod
    def _points_to_bbox(points, width, height, pad=0.12):
        if not points:
            return None
        xs = [min(width - 1, max(0, int(pt[0] * width))) for pt in points]
        ys = [min(height - 1, max(0, int(pt[1] * height))) for pt in points]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        if x2 <= x1 or y2 <= y1:
            return None
        dx = int((x2 - x1) * pad)
        dy = int((y2 - y1) * pad)
        x1 = max(0, x1 - dx)
        y1 = max(0, y1 - dy)
        x2 = min(width - 1, x2 + dx)
        y2 = min(height - 1, y2 + dy)
        return (x1, y1, x2, y2)

    def _detect_feature_regions(self, frame):
        if not self._absence_uses_features:
            return []

        if self.model_key == "gloves":
            return self._detect_hand_regions(frame)
        if self.model_key == "goggles":
            return self._detect_eye_regions(frame)
        if self.model_key == "boots":
            return self._detect_foot_regions(frame)
        return []

    def _detect_hand_regions(self, frame):
        if self._mp_hands is None:
            return []
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with self._feature_lock:
            res = self._mp_hands.process(frame_rgb)
        if not res.multi_hand_landmarks:
            return []

        h, w = frame.shape[:2]
        out = []
        for hand in res.multi_hand_landmarks:
            points = [(lm.x, lm.y) for lm in hand.landmark]
            bbox = self._points_to_bbox(points, w, h, pad=0.15)
            if bbox is not None:
                out.append(bbox)
        return out

    def _detect_eye_regions(self, frame):
        if self._mp_face_mesh is None:
            return []
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with self._feature_lock:
            res = self._mp_face_mesh.process(frame_rgb)
        if not res.multi_face_landmarks:
            return []

        h, w = frame.shape[:2]
        out = []
        for face in res.multi_face_landmarks:
            left_points = [(face.landmark[idx].x, face.landmark[idx].y) for idx in _LEFT_EYE_LANDMARKS]
            right_points = [(face.landmark[idx].x, face.landmark[idx].y) for idx in _RIGHT_EYE_LANDMARKS]
            left_bbox = self._points_to_bbox(left_points, w, h, pad=0.25)
            right_bbox = self._points_to_bbox(right_points, w, h, pad=0.25)
            if left_bbox is not None:
                out.append(left_bbox)
            if right_bbox is not None:
                out.append(right_bbox)
        return out

    def _detect_foot_regions(self, frame):
        if self._mp_pose is None:
            return []
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with self._feature_lock:
            res = self._mp_pose.process(frame_rgb)

        if not res.pose_landmarks:
            return []

        h, w = frame.shape[:2]
        landmarks = res.pose_landmarks.landmark
        left_triplet = (
            mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value,
            mp.solutions.pose.PoseLandmark.LEFT_HEEL.value,
            mp.solutions.pose.PoseLandmark.LEFT_FOOT_INDEX.value,
        )
        right_triplet = (
            mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value,
            mp.solutions.pose.PoseLandmark.RIGHT_HEEL.value,
            mp.solutions.pose.PoseLandmark.RIGHT_FOOT_INDEX.value,
        )

        out = []
        for triplet in (left_triplet, right_triplet):
            points = []
            for idx in triplet:
                lm = landmarks[idx]
                if getattr(lm, "visibility", 1.0) < _FOOT_LANDMARK_VISIBILITY_THRESHOLD:
                    continue
                points.append((lm.x, lm.y))
            if len(points) < 2:
                continue
            bbox = self._points_to_bbox(points, w, h, pad=0.35)
            if bbox is not None:
                out.append(bbox)
        return out

    @staticmethod
    def _is_footwear_label(label: str) -> bool:
        normalized = _normalize_label(label)
        return any(hint in normalized for hint in _FOOTWEAR_LABEL_HINTS)

    def _infer_boot_presence(self, foot_crop):
        try:
            region_results = self._model(foot_crop, conf=0.25, verbose=False)
        except Exception:
            return False, 0.0, ""

        first = region_results[0]
        names = first.names or {}
        probs = getattr(first, "probs", None)
        if probs is not None:
            top_index = int(probs.top1)
            top_confidence = float(probs.top1conf)
            top_label = _normalize_label(str(names.get(top_index, "")))
            return self._is_footwear_label(top_label), top_confidence, top_label

        best_confidence = 0.0
        best_label = ""
        boxes = getattr(first, "boxes", None)
        if boxes is None:
            return False, best_confidence, best_label

        for box in boxes:
            class_id = int(box.cls[0]) if box.cls is not None else -1
            class_name = _normalize_label(str(names.get(class_id, "")))
            confidence = float(box.conf[0]) if box.conf is not None else 0.0
            if confidence > best_confidence:
                best_confidence = confidence
                best_label = class_name
            if self._is_footwear_label(class_name):
                return True, confidence, class_name
        return False, best_confidence, best_label

    def _infer_boots_with_feature_regions(self, frame, camera_id: int = 0) -> Dict:
        feature_boxes = self._detect_foot_regions(frame)

        annotation_boxes = []
        present_confidences = []
        missing_confidences = []
        count = 0

        for fx1, fy1, fx2, fy2 in feature_boxes:
            crop = frame[fy1:fy2, fx1:fx2]
            if crop.size == 0:
                continue

            has_boots, confidence, raw_label = self._infer_boot_presence(crop)
            if has_boots:
                count += 1
                present_confidences.append(confidence)
                annotation_boxes.append(
                    {
                        "x1": int(fx1),
                        "y1": int(fy1),
                        "x2": int(fx2),
                        "y2": int(fy2),
                        "label": raw_label or "boots",
                        "color": "green",
                    }
                )
            else:
                missing_confidence = max(_FEATURE_MISSING_CONFIDENCE, 1.0 - confidence)
                missing_confidences.append(missing_confidence)
                annotation_boxes.append(
                    {
                        "x1": int(fx1),
                        "y1": int(fy1),
                        "x2": int(fx2),
                        "y2": int(fy2),
                        "label": "no boots",
                        "color": "red",
                    }
                )

        missing_count = len([box for box in annotation_boxes if box["color"] == "red"])
        detected = missing_count > 0
        confidence = (
            max(missing_confidences, default=0.0)
            if detected
            else max(present_confidences, default=0.0)
        )

        payload = {
            "count": count,
            "missing_count": missing_count,
            "feature_count": len(feature_boxes),
            "feature_missing_count": missing_count,
            "person_count": len(feature_boxes),
            "person_missing_count": missing_count,
            "absence_detector": "mediapipe+ultralytics_pretrained",
            "supports_explicit_missing_classes": False,
            "used_person_overlap_fallback": False,
            "ok_count": count,
            "boxes": annotation_boxes,
            "classification": (
                "ppe_missing"
                if detected
                else ("ppe_ok" if count > 0 else "no_target_detected")
            ),
            "model_classes": self.model_classes,
            "matched_target_labels": self.matched_labels,
            "camera_id": camera_id,
        }

        return {
            "status": "ok",
            "detected": detected,
            "confidence": round(confidence, 4),
            "payload": payload,
        }

    def _load_person_model_for_absence(self):
        if self._person_model is not None:
            return
        if not self.person_model_path:
            self.load_error = (
                f"{self.load_error}; " if self.load_error else ""
            ) + "Person fallback disabled: person model path not configured"
            return
        if not os.path.exists(self.person_model_path):
            self.load_error = (
                f"{self.load_error}; " if self.load_error else ""
            ) + (
                f"Person fallback model missing at {self.person_model_path}. "
                "Ensure Git LFS model files are present and run 'git lfs pull'."
            )
            return
        try:
            self._person_model = YOLO(self.person_model_path)
        except Exception as exc:
            self.load_error = (
                f"{self.load_error}; " if self.load_error else ""
            ) + f"Person fallback model load failed: {exc}"

    def _detect_person_regions(self, frame):
        if self._person_model is None:
            return []
        try:
            person_results = self._person_model(frame, classes=[0], conf=0.35, verbose=False)
            out = []
            for box in person_results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                out.append((x1, y1, x2, y2, float(box.conf[0])))
            return out
        except Exception:
            return []

    def _extract_qr(self, frame, boxes) -> str:
        if self._qr_detector is None or len(boxes) == 0:
            return ""

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            if x2 <= x1 or y2 <= y1:
                continue

            roi = frame[y1:y2, x1:x2]
            data, _, _ = self._qr_detector.detectAndDecode(roi)
            if data:
                return data

        data, _, _ = self._qr_detector.detectAndDecode(frame)
        return data or ""

    def infer(self, frame, camera_id: int = 0) -> Dict:
        if not self.available:
            return {
                "status": "unavailable",
                "detected": False,
                "confidence": 0.0,
                "payload": {
                    "message": "Model weights are not available for this adapter.",
                    "load_error": self.load_error,
                },
            }

        if self.model_key == "boots":
            return self._infer_boots_with_feature_regions(frame, camera_id=camera_id)

        try:
            results = self._model(frame, conf=0.35, verbose=False)
            boxes = results[0].boxes
            names = results[0].names or {}
            selected_confidences = []
            selected_boxes = []
            selected_box_coords = []
            selected_box_labels = []
            missing_confidences = []

            for box in boxes:
                class_id = int(box.cls[0]) if box.cls is not None else -1
                class_name = str(names.get(class_id, "")).lower()
                normalized_class_name = _normalize_label(class_name)
                if self.normalized_target_labels and normalized_class_name not in self.normalized_target_labels:
                    continue
                selected_boxes.append(box)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                selected_box_coords.append((x1, y1, x2, y2))
                selected_box_labels.append(normalized_class_name if normalized_class_name else "detected")
                confidence = float(box.conf[0])
                selected_confidences.append(confidence)
                if _is_missing_label(normalized_class_name):
                    missing_confidences.append(confidence)

            count = len(selected_boxes)

            annotation_boxes = []
            for box_coords, class_name in zip(selected_box_coords, selected_box_labels):
                x1, y1, x2, y2 = box_coords
                is_missing = _is_missing_label(class_name)
                annotation_boxes.append(
                    {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "label": class_name,
                        "color": "red" if is_missing else "green",
                    }
                )

            feature_count = 0
            feature_missing_count = 0
            feature_missing_confidences = []
            person_count = 0
            person_missing_count = 0
            person_missing_confidences = []
            used_person_overlap_fallback = False

            if self._absence_uses_features:
                feature_boxes = self._detect_feature_regions(frame)
                feature_count = len(feature_boxes)

                ppe_present_boxes = [
                    (b["x1"], b["y1"], b["x2"], b["y2"])
                    for b in annotation_boxes
                    if b["color"] == "green"
                ]

                for fx1, fy1, fx2, fy2 in feature_boxes:
                    feature_box = (fx1, fy1, fx2, fy2)
                    has_ppe = any(
                        _box_center_inside(ppe_box, feature_box) or _iou(feature_box, ppe_box) > 0.03
                        for ppe_box in ppe_present_boxes
                    )
                    if not has_ppe:
                        feature_missing_count += 1
                        feature_missing_confidences.append(_FEATURE_MISSING_CONFIDENCE)
                        annotation_boxes.append(
                            {
                                "x1": int(fx1),
                                "y1": int(fy1),
                                "x2": int(fx2),
                                "y2": int(fy2),
                                "label": f"no {self.model_key}",
                                "color": "red",
                            }
                        )

            explicit_missing_from_model = len(missing_confidences)
            should_run_person_fallback = (
                self._absence_uses_person_overlap
                and (
                    not self._supports_explicit_missing_classes
                    or explicit_missing_from_model == 0
                )
            )

            if should_run_person_fallback:
                person_boxes = self._detect_person_regions(frame)
                person_count = len(person_boxes)
                if person_boxes:
                    used_person_overlap_fallback = True
                ppe_present_boxes = [
                    (b["x1"], b["y1"], b["x2"], b["y2"])
                    for b in annotation_boxes
                    if b["color"] == "green"
                ]

                for px1, py1, px2, py2, pconf in person_boxes:
                    person_box = (px1, py1, px2, py2)
                    has_ppe = any(
                        _box_center_inside(ppe_box, person_box) or _iou(person_box, ppe_box) > 0.03
                        for ppe_box in ppe_present_boxes
                    )
                    if not has_ppe:
                        person_missing_count += 1
                        person_missing_confidences.append(
                            max(float(pconf), _PERSON_FALLBACK_MISSING_CONFIDENCE)
                        )
                        annotation_boxes.append(
                            {
                                "x1": int(px1),
                                "y1": int(py1),
                                "x2": int(px2),
                                "y2": int(py2),
                                "label": f"no {self.model_key}",
                                "color": "red",
                            }
                        )

            explicit_missing_count = len([b for b in annotation_boxes if b["color"] == "red"])
            missing_count = max(explicit_missing_count, feature_missing_count, person_missing_count)
            detected = missing_count > 0
            confidence = (
                max(missing_confidences + feature_missing_confidences + person_missing_confidences, default=0.0)
                if detected
                else max(selected_confidences, default=0.0)
            )

            if self._absence_uses_features:
                absence_detector = "mediapipe"
            elif self._supports_explicit_missing_classes and used_person_overlap_fallback:
                absence_detector = "model_labels+person_overlap_fallback"
            elif used_person_overlap_fallback:
                absence_detector = "person_overlap_fallback"
            else:
                absence_detector = "model_labels"

            payload = {
                "count": count,
                "missing_count": missing_count,
                "feature_count": feature_count,
                "feature_missing_count": feature_missing_count,
                "person_count": person_count if person_count else feature_count,
                "person_missing_count": person_missing_count if person_count else feature_missing_count,
                "absence_detector": absence_detector,
                "supports_explicit_missing_classes": bool(self._supports_explicit_missing_classes),
                "used_person_overlap_fallback": bool(used_person_overlap_fallback),
                "ok_count": len([b for b in annotation_boxes if b["color"] == "green"]),
                "boxes": annotation_boxes,
                "classification": (
                    "ppe_missing"
                    if detected
                    else ("ppe_ok" if count > 0 else "no_target_detected")
                ),
                "model_classes": self.model_classes,
                "matched_target_labels": self.matched_labels,
            }
            if self.supports_qr and count > 0:
                vest_qr = self._extract_qr(frame, selected_boxes)
                payload["vest_id"] = vest_qr or None
            payload["camera_id"] = camera_id

            return {
                "status": "ok",
                "detected": detected,
                "confidence": round(confidence, 4),
                "payload": payload,
            }
        except Exception as exc:
            return {
                "status": "error",
                "detected": False,
                "confidence": 0.0,
                "payload": {"error": str(exc)},
            }


class HelmetModelAdapter(PPEModelAdapter):
    def __init__(self, model_key: str, model_info: Dict):
        self.person_model_path = model_info.get("person_model_path")
        self._person_model = None
        super().__init__(model_key, model_info)

    def _load(self):
        super()._load()
        if not self.available:
            return

        if not self.person_model_path:
            self.available = False
            self.load_error = "Person model path is not configured"
            return

        if not os.path.exists(self.person_model_path):
            self.load_error = (
                f"Person model missing at {self.person_model_path}. "
                "Ensure model files are checked out with Git LFS ('git lfs pull')."
            )
            self.available = False
            return

        try:
            self._person_model = YOLO(self.person_model_path)
        except Exception as exc:
            self.available = False
            self.load_error = f"Failed to load person model: {exc}"

    def infer(self, frame, camera_id: int = 0) -> Dict:
        if not self.available or self._person_model is None:
            return {
                "status": "unavailable",
                "detected": False,
                "confidence": 0.0,
                "payload": {"message": "Helmet/person model pipeline unavailable", "load_error": self.load_error},
            }

        try:
            helmet_results = self._model(frame, conf=0.35, verbose=False)
            person_results = self._person_model(frame, classes=[0], conf=0.35, verbose=False)
            helmet_boxes = [
                tuple(map(int, box.xyxy[0])) + (float(box.conf[0]),)
                for box in helmet_results[0].boxes
            ]
            person_boxes = [
                tuple(map(int, box.xyxy[0])) + (float(box.conf[0]),)
                for box in person_results[0].boxes
            ]

            no_helmet_conf = []
            missing_boxes = []
            for px1, py1, px2, py2, pconf in person_boxes:
                has_helmet = False
                person_box = (px1, py1, px2, py2)
                head_region = (px1, py1, px2, py1 + int(max(1, (py2 - py1) * 0.38)))
                for hx1, hy1, hx2, hy2, _ in helmet_boxes:
                    helmet_box = (hx1, hy1, hx2, hy2)
                    if _iou(person_box, helmet_box) > 0.02 or _iou(head_region, helmet_box) > 0.08:
                        has_helmet = True
                        break
                if not has_helmet:
                    no_helmet_conf.append(float(pconf))
                    missing_boxes.append((px1, py1, px2, py2))

            no_helmet_count = len(no_helmet_conf)
            confidence = max(no_helmet_conf) if no_helmet_conf else 0.0
            annotation_boxes = []
            for hx1, hy1, hx2, hy2, _ in helmet_boxes:
                annotation_boxes.append(
                    {
                        "x1": int(hx1),
                        "y1": int(hy1),
                        "x2": int(hx2),
                        "y2": int(hy2),
                        "label": "helmet",
                        "color": "green",
                    }
                )
            for px1, py1, px2, py2, _ in person_boxes:
                annotation_boxes.append(
                    {
                        "x1": int(px1),
                        "y1": int(py1),
                        "x2": int(px2),
                        "y2": int(py2),
                        "label": "worker",
                        "color": "blue",
                    }
                )
            for mx1, my1, mx2, my2 in missing_boxes:
                annotation_boxes.append(
                    {
                        "x1": int(mx1),
                        "y1": int(my1),
                        "x2": int(mx2),
                        "y2": int(my2),
                        "label": "helmet missing",
                        "color": "red",
                    }
                )
            return {
                "status": "ok",
                "detected": no_helmet_count > 0,
                "confidence": round(confidence, 4),
                "payload": {
                    "person_count": len(person_boxes),
                    "helmet_count": len(helmet_boxes),
                    "no_helmet_count": no_helmet_count,
                    "classification": "helmet_missing" if no_helmet_count > 0 else "helmet_ok",
                    "camera_id": camera_id,
                    "boxes": annotation_boxes,
                },
            }
        except Exception as exc:
            return {
                "status": "error",
                "detected": False,
                "confidence": 0.0,
                "payload": {"error": str(exc)},
            }


class FatigueModelAdapter:
    def __init__(self, model_key: str, model_info: Dict):
        self.model_key = model_key
        self.display_name = model_info["display_name"]
        self.description = model_info["description"]
        self.weights_path = model_info["weights_path"]
        self.shape_predictor_path = model_info.get("shape_predictor_path")
        self.available = False
        self.load_error = None
        self._engine = None
        self._fatigue_consecutive_by_camera = {}
        self._load()

    def _load(self):
        if FatigueHybridEngine is None:
            self.load_error = f"Fatigue dependencies unavailable: {fatigue_import_error}"
            return

        if not os.path.exists(self.weights_path):
            self.load_error = (
                f"Fatigue model missing at {self.weights_path}. "
                "Ensure model files are checked out with Git LFS ('git lfs pull')."
            )
            return
        if not self.shape_predictor_path or not os.path.exists(self.shape_predictor_path):
            self.load_error = (
                f"Shape predictor missing at {self.shape_predictor_path}. "
                "Facial plotting is required for fatigue scoring. "
                "Ensure model files are checked out with Git LFS ('git lfs pull')."
            )
            return

        try:
            self._engine = FatigueHybridEngine(
                model_path=self.weights_path,
                shape_predictor_path=self.shape_predictor_path,
                head_tilt_alert_degrees=HEAD_TILT_ALERT_DEGREES,
            )
            self.available = True
        except Exception as exc:
            self.available = False
            self.load_error = str(exc)

    def infer(self, frame, camera_id: int = 0) -> Dict:
        if not self.available or self._engine is None:
            return {
                "status": "unavailable",
                "detected": False,
                "confidence": 0.0,
                "payload": {"message": "Fatigue model pipeline unavailable", "load_error": self.load_error},
            }

        try:
            analysis = self._engine.analyze(frame)
            if analysis["status"] != "ok":
                self._fatigue_consecutive_by_camera[camera_id] = 0
                return {
                    "status": analysis["status"],
                    "detected": False,
                    "confidence": 0.0,
                    "payload": analysis,
                }

            previous = self._fatigue_consecutive_by_camera.get(camera_id, 0)
            forced_fatigue_state = bool(analysis.get("forced_fatigue_state"))
            if analysis["is_fatigued"] or forced_fatigue_state:
                previous += 1
            else:
                previous = 0
            self._fatigue_consecutive_by_camera[camera_id] = previous

            sustained_fatigue = previous >= FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD
            head_tilt_exceeded = bool(analysis["head_tilt_exceeded"])
            # Forced fatigue (hard eye closure) triggers immediately; otherwise sustained hybrid fatigue.
            detected = forced_fatigue_state or sustained_fatigue

            reason = []
            if forced_fatigue_state:
                reason.append("forced_eye_closure")
            if sustained_fatigue:
                reason.append("sustained_fatigue")
            if head_tilt_exceeded:
                reason.append("head_tilt")
            if not reason:
                reason.append("monitoring")

            confidence = analysis["hybrid_score"]

            payload = {
                **analysis,
                "consecutive_fatigue_frames": previous,
                "fatigue_frame_threshold": FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD,
                "trigger_reason": reason,
            }
            return {
                "status": "ok",
                "detected": detected,
                "confidence": round(float(confidence), 4),
                "payload": payload,
            }
        except Exception as exc:
            return {
                "status": "error",
                "detected": False,
                "confidence": 0.0,
                "payload": {"error": str(exc)},
            }


class InferenceService:
    def __init__(self, model_definitions: Dict):
        self._adapters = {}
        for model_key, model_info in model_definitions.items():
            if model_key == "helmet":
                adapter = HelmetModelAdapter(model_key, model_info)
            elif model_key == "fatigue":
                adapter = FatigueModelAdapter(model_key, model_info)
            else:
                adapter = PPEModelAdapter(model_key, model_info)
            self._adapters[model_key] = adapter

    def get_model_health(self, model_key: str) -> Dict:
        adapter = self._adapters[model_key]
        return {
            "available": adapter.available,
            "load_error": adapter.load_error,
            "model_classes": list(getattr(adapter, "model_classes", []) or []),
            "matched_target_labels": list(getattr(adapter, "matched_labels", []) or []),
            "configured_target_labels": sorted(getattr(adapter, "normalized_target_labels", []) or []),
        }

    def run_models(self, frame, model_keys: List[str], camera_id: int = 0) -> List[Dict]:
        results = []
        for model_key in model_keys:
            adapter = self._adapters[model_key]
            inference = adapter.infer(frame, camera_id=camera_id)
            results.append(
                {
                    "model_key": model_key,
                    "model_name": adapter.display_name,
                    "status": inference["status"],
                    "detected": bool(inference["detected"]),
                    "confidence": float(inference["confidence"]),
                    "payload": inference["payload"],
                }
            )
        return results
