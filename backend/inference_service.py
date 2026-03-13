import base64
import bz2
import os
import re
import urllib.request
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


def decode_base64_image(image_base64: str):
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _download_any(download_urls: List[str], destination_path: str) -> str:
    if not download_urls:
        return ""

    last_error = ""
    destination_dir = os.path.dirname(destination_path)
    if destination_dir:
        os.makedirs(destination_dir, exist_ok=True)

    for url in download_urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                raw_bytes = response.read()

            if url.lower().endswith(".bz2"):
                raw_bytes = bz2.decompress(raw_bytes)

            with open(destination_path, "wb") as out_file:
                out_file.write(raw_bytes)
            return ""
        except Exception as exc:
            last_error = str(exc)
    return last_error or "No downloadable URL succeeded"


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
        self.download_urls = model_info.get("download_urls", [])
        self.target_labels = {label.lower() for label in model_info.get("target_labels", [])}
        self.normalized_target_labels = {
            _normalize_label(label) for label in model_info.get("target_labels", [])
        }
        self.strict_target_match = bool(model_info.get("strict_target_match", True))
        self.supports_qr = model_key == "vest"

        self.available = False
        self.load_error = None
        self.download_error = None
        self.downloaded = False
        self._model = None
        self.model_classes = []
        self.matched_labels = []
        self._qr_detector = cv2.QRCodeDetector() if self.supports_qr else None
        self._load()

    def _download_weights_if_missing(self):
        if os.path.exists(self.weights_path):
            return
        error = _download_any(self.download_urls, self.weights_path)
        if error:
            self.download_error = error
            return
        self.downloaded = True

    def _load(self):
        self._download_weights_if_missing()
        if not os.path.exists(self.weights_path):
            if self.download_error:
                self.load_error = (
                    f"Weights missing at {self.weights_path}. Download failed: {self.download_error}"
                )
            else:
                self.load_error = f"Weights missing at {self.weights_path}"
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
            self.available = True
        except Exception as exc:
            self.available = False
            self.load_error = str(exc)

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

        try:
            results = self._model(frame, conf=0.35, verbose=False)
            boxes = results[0].boxes
            names = results[0].names or {}
            selected_confidences = []
            selected_boxes = []
            selected_box_labels = []
            missing_confidences = []

            for box in boxes:
                class_id = int(box.cls[0]) if box.cls is not None else -1
                class_name = str(names.get(class_id, "")).lower()
                normalized_class_name = _normalize_label(class_name)
                if self.normalized_target_labels and normalized_class_name not in self.normalized_target_labels:
                    continue
                selected_boxes.append(box)
                selected_box_labels.append(normalized_class_name if normalized_class_name else "detected")
                confidence = float(box.conf[0])
                selected_confidences.append(confidence)
                if _is_missing_label(normalized_class_name):
                    missing_confidences.append(confidence)

            count = len(selected_boxes)

            annotation_boxes = []
            for box, class_name in zip(selected_boxes, selected_box_labels):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
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

            missing_count = len([b for b in annotation_boxes if b["color"] == "red"])
            detected = missing_count > 0
            confidence = (
                max(missing_confidences, default=0.0)
                if detected
                else max(selected_confidences, default=0.0)
            )
            payload = {
                "count": count,
                "missing_count": missing_count,
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
        self.person_download_urls = model_info.get("person_download_urls", [])
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
            person_error = _download_any(self.person_download_urls, self.person_model_path)
            if person_error:
                self.load_error = (
                    f"Person model missing at {self.person_model_path}. Download failed: {person_error}"
                )
                self.available = False
                return
            self.downloaded = True

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
        self.download_urls = model_info.get("download_urls", [])
        self.shape_predictor_path = model_info.get("shape_predictor_path")
        self.shape_download_urls = model_info.get("shape_download_urls", [])
        self.available = False
        self.load_error = None
        self.download_error = None
        self.downloaded = False
        self._engine = None
        self._fatigue_consecutive_by_camera = {}
        self._load()

    def _download_dependencies_if_missing(self):
        if not os.path.exists(self.weights_path):
            error = _download_any(self.download_urls, self.weights_path)
            if error:
                self.download_error = error
            else:
                self.downloaded = True

        if self.shape_predictor_path and not os.path.exists(self.shape_predictor_path):
            error = _download_any(self.shape_download_urls, self.shape_predictor_path)
            if error and not self.download_error:
                self.download_error = error
            elif not error:
                self.downloaded = True

    def _load(self):
        if FatigueHybridEngine is None:
            self.load_error = f"Fatigue dependencies unavailable: {fatigue_import_error}"
            return

        self._download_dependencies_if_missing()
        if not os.path.exists(self.weights_path):
            self.load_error = f"Fatigue model missing at {self.weights_path}"
            if self.download_error:
                self.load_error += f". Download failed: {self.download_error}"
            return
        if not self.shape_predictor_path or not os.path.exists(self.shape_predictor_path):
            self.load_error = (
                f"Shape predictor missing at {self.shape_predictor_path}. "
                "Facial plotting is required for fatigue scoring."
            )
            if self.download_error:
                self.load_error += f" Download failed: {self.download_error}"
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
            if analysis["is_fatigued"]:
                previous += 1
            else:
                previous = 0
            self._fatigue_consecutive_by_camera[camera_id] = previous

            sustained_fatigue = previous >= FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD
            head_tilt_exceeded = bool(analysis["head_tilt_exceeded"])
            # Classification driven by hybrid formula; head tilt is informational only
            detected = sustained_fatigue

            reason = []
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
            "downloaded": getattr(adapter, "downloaded", False),
            "download_error": getattr(adapter, "download_error", None),
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
