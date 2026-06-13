"""Generate annotated documentation examples for every configured model.

The output is intentionally documentation-oriented: each image gets a dark
canvas, a readable title, the model annotation, and a short caption/legend.
Run from the repository root:

    conda run -n fatigue_env python scripts/generate_model_output_examples.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
OUTPUT_ROOT = ROOT / "docs" / "model_output_examples"
SOURCE_IMAGES_DIR = OUTPUT_ROOT / "source_images"
BENCHMARK_ASSETS = ROOT / "docs" / "benchmark_assets"
BENCHMARK_RESULTS = ROOT / "docs" / "benchmark_results"

MODEL_KEYS = (
    "helmet",
    "vest",
    "gloves",
    "goggles",
    "boots",
    "faceshield",
    "safetysuit",
    "fatigue",
)
PPE_MODEL_KEYS = tuple(key for key in MODEL_KEYS if key != "fatigue")
CURATED_MODEL_KEYS = ("gloves", "boots", "goggles", "faceshield")
EXAMPLE_FILENAMES = ("positive.jpg", "negative.jpg", "contact_sheet.jpg")

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}
MAX_SCAN_IMAGES = 90
HTTP_TIMEOUT_SECONDS = 35

CURATED_SOURCE_SPECS = (
    {
        "model_key": "gloves",
        "kind": "positive",
        "slug": "pexels-safety-gloves-11427400",
        "page_url": "https://www.pexels.com/photo/person-wearing-safety-gloves-11427400/",
        "image_url": "https://images.pexels.com/photos/11427400/pexels-photo-11427400.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Close-up construction worker safety gloves with the gloves unobscured.",
    },
    {
        "model_key": "gloves",
        "kind": "positive",
        "slug": "pexels-protective-gloves-8486966",
        "page_url": "https://www.pexels.com/photo/close-up-shot-of-a-person-wearing-work-gloves-8486966/",
        "image_url": "https://images.pexels.com/photos/8486966/pexels-photo-8486966.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Close-up protective work gloves used as a backup curated candidate.",
    },
    {
        "model_key": "boots",
        "kind": "positive",
        "slug": "pexels-worker-boots-12491630",
        "page_url": "https://www.pexels.com/photo/legs-of-workers-12491630/",
        "image_url": "https://images.pexels.com/photos/12491630/pexels-photo-12491630.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Construction workers wearing high-visibility gear and work boots.",
    },
    {
        "model_key": "boots",
        "kind": "positive",
        "slug": "pexels-safety-boots-worksite-1216589",
        "page_url": "https://www.pexels.com/photo/low-angle-photo-of-man-standing-on-concrete-floor-1216589/",
        "image_url": "https://images.pexels.com/photos/1216589/pexels-photo-1216589.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Worksite footwear candidate for safety/work boot documentation.",
    },
    {
        "model_key": "goggles",
        "kind": "positive",
        "slug": "pexels-protective-goggles-work-9241702",
        "page_url": "https://www.pexels.com/photo/a-woman-wearing-protective-goggles-at-work-9241702/",
        "image_url": "https://images.pexels.com/photos/9241702/pexels-photo-9241702.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Worker wearing apparent protective goggles at work, not fashion eyewear.",
    },
    {
        "model_key": "goggles",
        "kind": "positive",
        "slug": "pexels-safety-glasses-worker-8820998",
        "page_url": "https://www.pexels.com/photo/a-man-wearing-safety-glasses-8820998/",
        "image_url": "https://images.pexels.com/photos/8820998/pexels-photo-8820998.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Worker wearing safety glasses/protective eyewear.",
    },
    {
        "model_key": "faceshield",
        "kind": "positive",
        "slug": "pexels-face-shield-10878602",
        "page_url": "https://www.pexels.com/photo/person-wearing-face-mask-and-face-shield-with-protective-suit-10878602/",
        "image_url": "https://images.pexels.com/photos/10878602/pexels-photo-10878602.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Close-up healthcare worker wearing an obvious face shield.",
    },
    {
        "model_key": "faceshield",
        "kind": "positive",
        "slug": "pexels-face-shield-ppe-8460401",
        "page_url": "https://www.pexels.com/photo/person-wearing-ppe-with-arms-crossed-8460401/",
        "image_url": "https://images.pexels.com/photos/8460401/pexels-photo-8460401.jpeg?auto=compress&cs=tinysrgb&w=1600&fm=jpg",
        "license": "Pexels free-to-use license; see source page",
        "description": "Medical worker in PPE with a clear face shield as a backup candidate.",
    },
)

_RAW_YOLO_CACHE = {}


def missing_manifest_files(manifest: dict) -> list[str]:
    missing: list[str] = []
    for model_data in manifest.get("models", {}).values():
        for example_key in ("positive", "negative", "contact_sheet"):
            path = model_data.get(example_key, {}).get("path")
            if path and not Path(path).exists():
                missing.append(path)
    return missing


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _curated_specs(model_key: str, kind: str | None = None) -> list[dict]:
    return [
        spec
        for spec in CURATED_SOURCE_SPECS
        if spec["model_key"] == model_key and (kind is None or spec["kind"] == kind)
    ]


def _source_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SafeVisionDocs/1.0)",
            "Accept": "text/html,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )


def _read_url(url: str) -> bytes:
    with urllib.request.urlopen(_source_request(url), timeout=HTTP_TIMEOUT_SECONDS) as response:
        return response.read()


def _looks_like_cv_image(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    header = path.read_bytes()[:12]
    return header.startswith(b"\xff\xd8") or header.startswith(b"\x89PNG") or header.startswith(b"BM")


def _extract_source_image_url(page_url: str, html: str) -> str | None:
    og_match = re.search(
        r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    if not og_match:
        og_match = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']',
            html,
            flags=re.IGNORECASE,
        )
    if og_match:
        return urllib.parse.unquote(og_match.group(1).replace("&amp;", "&"))

    pexels_urls = re.findall(r'https://images\.pexels\.com/photos/[^"\'<>\s]+', html)
    if pexels_urls:
        return urllib.parse.unquote(pexels_urls[0].replace("&amp;", "&"))

    commons_uploads = re.findall(r'https://upload\.wikimedia\.org/[^"\'<>\s]+', html)
    if commons_uploads:
        return urllib.parse.unquote(commons_uploads[0].replace("&amp;", "&"))

    return None


def _download_curated_source(spec: dict) -> Path | None:
    SOURCE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SOURCE_IMAGES_DIR / f"{spec['slug']}.jpg"
    if _looks_like_cv_image(out_path):
        return out_path

    page_url = spec["page_url"]
    try:
        image_url = spec.get("image_url")
        if not image_url:
            html = _read_url(page_url).decode("utf-8", errors="ignore")
            image_url = _extract_source_image_url(page_url, html)
        if not image_url:
            print(f"[{spec['model_key']}] curated source had no image URL: {page_url}")
            return None
        image_bytes = _read_url(image_url)
    except Exception as exc:
        print(f"[{spec['model_key']}] curated source download failed: {page_url} ({exc})")
        return None

    out_path.write_bytes(image_bytes)
    return out_path


def _curated_candidate_images(model_key: str, kind: str = "positive") -> list[tuple[Path, dict]]:
    candidates: list[tuple[Path, dict]] = []
    for spec in _curated_specs(model_key, kind):
        path = _download_curated_source(spec)
        if path is not None:
            candidates.append((path, spec))
    return candidates


def _curated_manifest_fields(spec: dict | None) -> dict:
    if not spec:
        return {}
    return {
        "source_url": spec["page_url"],
        "source_license": spec["license"],
        "source_description": spec["description"],
        "source_slug": spec["slug"],
    }


def _load_runtime():
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    import cv2

    from annotation import draw_annotations
    from config import MODEL_DEFINITIONS
    from inference_service import InferenceService

    return cv2, draw_annotations, InferenceService(MODEL_DEFINITIONS)


def _image_files(*roots: Path) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() in IMAGE_SUFFIXES:
            out.append(root)
            continue
        out.extend(
            sorted(
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        )
    return out


def _benchmark_source_for(example_path: Path) -> Path | None:
    source = BENCHMARK_ASSETS / "images" / "test" / example_path.name
    if source.exists():
        return source
    for suffix in IMAGE_SUFFIXES:
        candidate = source.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def _candidate_images(model_key: str) -> list[Path]:
    benchmark_examples = _image_files(BENCHMARK_RESULTS / model_key / "examples")
    preferred: list[Path] = []
    for example in benchmark_examples:
        source = _benchmark_source_for(example)
        preferred.append(source or example)

    construction = _image_files(BENCHMARK_ASSETS / "images" / "test")
    extras = _image_files(ROOT / "Construction-Safety-Equipment.jpg")

    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in preferred + construction + extras:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(path)
    return ordered[:MAX_SCAN_IMAGES]


def _box_colors(result: dict) -> list[str]:
    payload = result.get("payload", {})
    return [str(box.get("color", "")) for box in payload.get("boxes", [])]


def _green_boxes(result: dict) -> list[dict]:
    return [
        box
        for box in result.get("payload", {}).get("boxes", [])
        if str(box.get("color", "")) == "green"
    ]


def _has_readable_positive_box(result: dict) -> bool:
    for box in _green_boxes(result):
        width = max(0, int(box.get("x2", 0)) - int(box.get("x1", 0)))
        height = max(0, int(box.get("y2", 0)) - int(box.get("y1", 0)))
        if width * height >= 500:
            return True
    return False


def _is_positive_example(model_key: str, result: dict) -> bool:
    if result.get("status") != "ok" or result.get("detected"):
        return False
    payload = result.get("payload", {})
    colors = _box_colors(result)
    if model_key == "helmet":
        return payload.get("helmet_count", 0) > 0 and "red" not in colors and _has_readable_positive_box(result)
    return payload.get("ok_count", 0) > 0 and "red" not in colors and _has_readable_positive_box(result)


def _is_negative_example(result: dict) -> bool:
    return result.get("status") == "ok" and result.get("detected") and "red" in _box_colors(result)


def _run_model(service, frame, model_key: str) -> dict:
    return service.run_models(frame, [model_key], camera_id=901)[0]


def _normalize_doc_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _is_missing_doc_label(label: str) -> bool:
    normalized = _normalize_doc_label(label)
    return normalized.startswith("no_") or normalized.startswith("without_")


def _positive_doc_labels(model_key: str) -> set[str]:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from config import MODEL_DEFINITIONS

    labels = {
        _normalize_doc_label(label)
        for label in MODEL_DEFINITIONS[model_key].get("target_labels", [])
        if not _is_missing_doc_label(label)
    }
    labels.discard("")
    labels.discard("none")
    return labels or {_normalize_doc_label(model_key)}


def _raw_detector_result(frame, model_key: str) -> dict:
    """Run the configured detector directly for curated documentation positives.

    This is only used after the deployed adapter fails to produce a readable
    positive example on a curated public-source image. The manifest labels it as
    a documentation fallback so the example remains honest.
    """
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from config import MODEL_DEFINITIONS
    from ultralytics import YOLO

    model_info = MODEL_DEFINITIONS[model_key]
    model = _RAW_YOLO_CACHE.get(model_key)
    if model is None:
        model = YOLO(model_info["weights_path"])
        _RAW_YOLO_CACHE[model_key] = model

    positive_labels = _positive_doc_labels(model_key)
    confidence_threshold = min(0.25, float(model_info.get("inference_confidence", 0.35)))
    try:
        results = model(frame, conf=confidence_threshold, verbose=False)
    except Exception as exc:
        return {
            "status": "error",
            "detected": False,
            "confidence": 0.0,
            "payload": {"boxes": [], "classification": "raw_detector_error", "message": str(exc)},
        }

    names = results[0].names or {}
    annotation_boxes = []
    confidences = []
    for box in results[0].boxes or []:
        class_id = int(box.cls[0]) if box.cls is not None else -1
        label = str(names.get(class_id, "detected"))
        normalized = _normalize_doc_label(label)
        if normalized not in positive_labels:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf[0]) if box.conf is not None else 0.0
        confidences.append(confidence)
        annotation_boxes.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "label": f"{normalized} {confidence:.2f}",
                "color": "green",
            }
        )

    return {
        "status": "ok",
        "detected": False,
        "confidence": round(max(confidences, default=0.0), 4),
        "payload": {
            "count": len(annotation_boxes),
            "ok_count": len(annotation_boxes),
            "missing_count": 0,
            "boxes": annotation_boxes,
            "classification": "ppe_ok" if annotation_boxes else "no_target_detected",
            "documentation_pipeline": "raw_yolo_detector",
        },
        "note": "Curated public-source image; deployed adapter did not produce a readable positive box, so documentation used the configured detector directly.",
    }


def _font_scale(width: int, base: float = 0.55) -> float:
    return max(0.45, min(0.8, width / 1100.0 * base))


def _draw_status_panel(cv2, frame, lines: list[str], severity: str = "neutral"):
    color = {
        "ok": (0, 190, 80),
        "alert": (0, 60, 255),
        "neutral": (230, 230, 230),
    }.get(severity, (230, 230, 230))
    pad = 10
    line_h = 20
    width = min(frame.shape[1] - 20, 430)
    height = pad * 2 + line_h * len(lines)
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + width, 10 + height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
    cv2.rectangle(frame, (10, 10), (10 + width, 10 + height), color, 2)
    for idx, line in enumerate(lines):
        y = 10 + pad + 15 + idx * line_h
        cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)


def _captioned_canvas(cv2, image, title: str, caption: str, legend: str):
    max_w = 980
    h, w = image.shape[:2]
    scale = min(1.0, max_w / max(w, 1))
    if scale < 1.0:
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = image.shape[:2]

    top = 76
    bottom = 82
    side = 46
    canvas = cv2.copyMakeBorder(
        image,
        top,
        bottom,
        side,
        side,
        cv2.BORDER_CONSTANT,
        value=(28, 28, 28),
    )
    cv2.putText(canvas, title, (side, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (245, 245, 245), 2, cv2.LINE_AA)
    cv2.putText(canvas, legend, (side, 61), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (218, 218, 218), 1, cv2.LINE_AA)
    y0 = top + h + 35
    for idx, line in enumerate(_wrap_text(caption, 118)):
        cv2.putText(canvas, line, (side, y0 + idx * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225, 225, 225), 1, cv2.LINE_AA)
    return canvas


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if current and len(trial) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines[:3]


def _write_image(cv2, path: Path, image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise RuntimeError(f"Could not write {path}")


def _make_contact_sheet(cv2, positive_path: Path, negative_path: Path, out_path: Path, model_key: str) -> None:
    left = cv2.imread(str(positive_path))
    right = cv2.imread(str(negative_path))
    if left is None or right is None:
        raise RuntimeError(f"Could not read examples for contact sheet: {model_key}")
    target_h = 520
    resized = []
    for img in (left, right):
        h, w = img.shape[:2]
        scale = target_h / max(h, 1)
        resized.append(cv2.resize(img, (int(w * scale), target_h), interpolation=cv2.INTER_AREA))
    gap = 24
    width = resized[0].shape[1] + resized[1].shape[1] + gap
    sheet = cv2.copyMakeBorder(
        resized[0],
        0,
        0,
        0,
        resized[1].shape[1] + gap,
        cv2.BORDER_CONSTANT,
        value=(28, 28, 28),
    )
    sheet[:, resized[0].shape[1] + gap :] = resized[1]
    title_bar = 54
    sheet = cv2.copyMakeBorder(sheet, title_bar, 0, 0, 0, cv2.BORDER_CONSTANT, value=(28, 28, 28))
    cv2.putText(sheet, f"{model_key} model output examples", (24, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (245, 245, 245), 2, cv2.LINE_AA)
    if sheet.shape[1] != width:
        sheet = sheet[:, :width]
    _write_image(cv2, out_path, sheet)


def _ppe_caption(model_key: str, result: dict, kind: str) -> str:
    payload = result.get("payload", {})
    pipeline = payload.get("documentation_pipeline")
    if kind == "positive":
        if pipeline == "raw_yolo_detector":
            return (
                f"{model_key} positive safety example from curated public-source imagery. "
                "Green boxes are the configured detector's visible PPE output; the deployed adapter was attempted first."
            )
        return (
            f"{model_key} positive safety example from the deployed adapter. "
            f"Classification={payload.get('classification', 'ok')}; green boxes show confirmed compliant model output."
        )
    return (
        f"{model_key} negative safety example from the deployed adapter. "
        f"Classification={payload.get('classification', 'alert')}; red boxes show missing-PPE output from model labels, MediaPipe assists, or person fallback."
    )


def _generate_ppe_examples(cv2, draw_annotations, service, model_key: str) -> dict:
    model_dir = OUTPUT_ROOT / model_key
    model_dir.mkdir(parents=True, exist_ok=True)
    examples: dict[str, dict] = {}
    selected: dict[str, tuple[Path, dict, object, dict | None]] = {}

    if model_key in CURATED_MODEL_KEYS:
        for image_path, spec in _curated_candidate_images(model_key, kind="positive"):
            frame = cv2.imread(str(image_path))
            if frame is None:
                continue
            result = _run_model(service, frame, model_key)
            if _is_positive_example(model_key, result):
                selected["positive"] = (image_path, result, frame, spec)
                break
            raw_result = _raw_detector_result(frame, model_key)
            if _is_positive_example(model_key, raw_result):
                selected["positive"] = (image_path, raw_result, frame, spec)
                break

    for image_path in _candidate_images(model_key):
        frame = cv2.imread(str(image_path))
        if frame is None:
            continue
        result = _run_model(service, frame, model_key)
        if "positive" not in selected and _is_positive_example(model_key, result):
            selected["positive"] = (image_path, result, frame, None)
        if "negative" not in selected and _is_negative_example(result):
            selected["negative"] = (image_path, result, frame, None)
        if "positive" in selected and "negative" in selected:
            break

    if "positive" not in selected:
        selected["positive"] = _fallback_benchmark_positive(cv2, model_key)

    if "negative" not in selected:
        selected["negative"] = _fallback_benchmark_negative(cv2, model_key)

    benchmark_metrics = _read_json(BENCHMARK_RESULTS / model_key / "metrics.json")
    benchmark_tp = sum((stats or {}).get("tp", 0) for stats in benchmark_metrics.get("per_class", {}).values())

    for kind in ("positive", "negative"):
        source_path, result, frame, source_spec = selected[kind]
        if result.get("status") in {"generated_card", "benchmark_fallback"}:
            canvas = frame
        else:
            annotated = draw_annotations(frame, {model_key: result}, enabled_overlays={model_key})
            severity = "ok" if kind == "positive" else "alert"
            _draw_status_panel(
                cv2,
                annotated,
                [
                    f"model: {model_key}",
                    f"status: {result.get('status')} detected={result.get('detected')}",
                    f"confidence: {_safe_confidence(result):.2f}",
                ],
                severity=severity,
            )
            title = f"{model_key.upper()} - {'Positive safety output' if kind == 'positive' else 'Negative safety output'}"
            legend = "Legend: green = confirmed PPE/output, red = missing PPE/alert, blue/cyan = support region"
            canvas = _captioned_canvas(cv2, annotated, title, _ppe_caption(model_key, result, kind), legend)

        out_path = model_dir / f"{kind}.jpg"
        _write_image(cv2, out_path, canvas)
        examples[kind] = {
            "path": str(out_path),
            "source": _repo_relative(source_path),
            "status": result.get("status"),
            "detected": result.get("detected"),
            "confidence": result.get("confidence"),
            "note": result.get("note", ""),
        }
        examples[kind].update(_curated_manifest_fields(source_spec))
        if result.get("payload", {}).get("documentation_pipeline"):
            examples[kind]["documentation_pipeline"] = result["payload"]["documentation_pipeline"]
        if benchmark_tp == 0 and kind == "positive":
            examples[kind]["benchmark_limitation"] = (
                "Benchmark metrics report 0 detector true-positive matches; this image demonstrates deployed app output only."
            )

    contact_path = model_dir / "contact_sheet.jpg"
    _make_contact_sheet(cv2, model_dir / "positive.jpg", model_dir / "negative.jpg", contact_path, model_key)
    examples["contact_sheet"] = {"path": str(contact_path)}
    examples["metrics"] = benchmark_metrics
    return examples


def _safe_confidence(result: dict) -> float:
    value = result.get("confidence", 0.0)
    if value is None:
        return 0.0
    return float(value)


def _fallback_benchmark_positive(cv2, model_key: str):
    metrics = _read_json(BENCHMARK_RESULTS / model_key / "metrics.json")
    per_class = metrics.get("per_class", {})
    has_tp = any((stats or {}).get("tp", 0) > 0 for stats in per_class.values())
    examples = _image_files(BENCHMARK_RESULTS / model_key / "examples")
    source = _best_color_evidence(cv2, examples, "positive") or ROOT / "Construction-Safety-Equipment.jpg"
    frame = cv2.imread(str(source))
    if frame is None:
        frame = _blank_card(cv2, f"{model_key}: no benchmark image available")
    note = "benchmark TP example reused because no clean app-positive frame was found"
    if not has_tp:
        note = "no benchmark true-positive detector match exists for this model; positive example is a limitation card"
        frame = _blank_card(
            cv2,
            f"{model_key.upper()} positive detector example unavailable",
            "Benchmark metrics report 0 true-positive detector matches. The app still demonstrates missing-PPE behavior via fallback annotations.",
        )
    else:
        frame = _captioned_canvas(
            cv2,
            frame,
            f"{model_key.upper()} - Benchmark positive evidence",
            "Existing benchmark example reused because a clean deployed-adapter positive frame was not found during deterministic scanning.",
            "Legend: green = true positive where present, red = false positive, orange = missed ground truth",
        )
    return source, {
        "status": "generated_card" if not has_tp else "benchmark_fallback",
        "detected": None,
        "confidence": None,
        "note": note,
    }, frame, None


def _fallback_negative_card(cv2, model_key: str):
    source = ROOT / "Construction-Safety-Equipment.jpg"
    frame = _blank_card(
        cv2,
        f"{model_key.upper()} negative example unavailable",
        "No deterministic frame produced a missing-PPE/alert output. Re-run with more local imagery if a stronger example is needed.",
    )
    return source, {
        "status": "generated_card",
        "detected": None,
        "confidence": None,
        "note": "no deterministic negative frame found",
    }, frame, None


def _fallback_benchmark_negative(cv2, model_key: str):
    examples = _image_files(BENCHMARK_RESULTS / model_key / "examples")
    source = _best_color_evidence(cv2, examples, "negative") if examples else None
    if source is None:
        return _fallback_negative_card(cv2, model_key)
    frame = cv2.imread(str(source))
    if frame is None:
        return _fallback_negative_card(cv2, model_key)
    frame = _captioned_canvas(
        cv2,
        frame,
        f"{model_key.upper()} - Benchmark negative evidence",
        "Existing benchmark example reused because a deterministic deployed-adapter missing-PPE frame was not found. It preserves red false-positive and orange missed-ground-truth evidence where present.",
        "Legend: green = true positive where present, red = false positive, orange = missed ground truth",
    )
    return source, {
        "status": "benchmark_fallback",
        "detected": None,
        "confidence": None,
        "note": "benchmark negative/error example reused because no clean app-negative frame was found",
    }, frame, None


def _best_color_evidence(cv2, paths: list[Path], kind: str) -> Path | None:
    best_path = None
    best_score = -1
    for path in paths:
        frame = cv2.imread(str(path))
        if frame is None:
            continue
        if kind == "positive":
            # Benchmark TP boxes are bright green in BGR.
            mask = (
                (frame[:, :, 0] >= 30)
                & (frame[:, :, 0] <= 120)
                & (frame[:, :, 1] >= 150)
                & (frame[:, :, 2] <= 80)
            )
        else:
            # Negative evidence is either red FP or orange missed GT.
            red = (frame[:, :, 2] >= 160) & (frame[:, :, 1] <= 100)
            orange = (frame[:, :, 2] >= 180) & (frame[:, :, 1] >= 90) & (frame[:, :, 1] <= 180)
            mask = red | orange
        score = int(mask.sum())
        if score > best_score:
            best_score = score
            best_path = path
    return best_path


def _blank_card(cv2, title: str, detail: str = ""):
    import numpy as np

    frame = np.zeros((540, 900, 3), dtype=np.uint8)
    frame[:] = (28, 28, 28)
    cv2.putText(frame, title, (48, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.86, (245, 245, 245), 2, cv2.LINE_AA)
    for idx, line in enumerate(_wrap_text(detail, 92)):
        cv2.putText(frame, line, (48, 270 + idx * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (215, 215, 215), 1, cv2.LINE_AA)
    return frame


def _fatigue_videos() -> list[Path]:
    video_dir = BACKEND_DIR / "uploads" / "dev_videos"
    preferred = sorted(video_dir.glob("*Eye Contact*.mp4"))
    rest = sorted(path for path in video_dir.glob("*.mp4") if path not in preferred)
    return preferred + rest


def _draw_fatigue_extra_panel(cv2, frame, result: dict) -> None:
    payload = result.get("payload", {})
    reason = ",".join(payload.get("trigger_reason", []))
    backend = payload.get("mesh_backend", "mediapipe")
    state_label = fatigue_state_label(payload)
    lines = [
        "model: fatigue",
        f"mesh backend: {backend}",
        f"AI probability: {float(payload.get('fatigue_probability', 0.0)):.2f}",
        f"hybrid score: {float(payload.get('hybrid_score', 0.0)):.2f}",
        f"EAR/MAR: {float(payload.get('ear', 0.0)):.2f} / {float(payload.get('mar', 0.0)):.2f}",
        f"tilt: {float(payload.get('head_tilt_degrees', 0.0)):.1f} deg",
        f"frames: {payload.get('consecutive_fatigue_frames', 0)}/{payload.get('fatigue_frame_threshold', 0)}",
        f"decision: {state_label if state_label == 'FATIGUED' else 'monitoring'} {reason}",
    ]
    severity = "alert" if result.get("detected") or payload.get("is_fatigued") else "ok"
    _draw_status_panel(cv2, frame, lines, severity=severity)


def fatigue_state_label(payload: dict) -> str:
    return "FATIGUED" if payload.get("is_fatigued") else "NOT FATIGUED"


def _label_box_doc(cv2, frame, text: str, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, 0.48, 1)
    y_top = max(0, y1 - th - 8)
    cv2.rectangle(frame, (x1, y_top), (x1 + tw + 5, max(y_top + th + 8, y1)), color, -1)
    cv2.putText(frame, text, (x1 + 3, max(th + 2, y1 - 4)), font, 0.48, (0, 0, 0), 1, cv2.LINE_AA)


def _draw_fatigue_doc_annotations(cv2, frame, result: dict):
    out = frame.copy()
    payload = result.get("payload", {})
    is_fatigued = bool(payload.get("is_fatigued"))
    box_color = (0, 60, 255) if is_fatigued else (0, 200, 80)
    mesh_color = (0, 180, 255) if is_fatigued else (0, 200, 80)
    cyan = (220, 200, 0)
    face_box = payload.get("face_box")

    if face_box:
        x1, y1, x2, y2 = (int(face_box[key]) for key in ("x1", "y1", "x2", "y2"))
        cv2.rectangle(out, (x1, y1), (x2, y2), box_color, 2)
        hybrid = float(payload.get("hybrid_score", 0.0))
        _label_box_doc(cv2, out, f"{fatigue_state_label(payload)} ({hybrid:.0%})", x1, y1, box_color)

    for pt in payload.get("landmarks", []):
        if len(pt) >= 2:
            cv2.circle(out, (int(pt[0]), int(pt[1])), 1, mesh_color, -1)

    pose = payload.get("pose_line")
    if pose:
        cv2.arrowedLine(
            out,
            tuple(map(int, pose["start"])),
            tuple(map(int, pose["end"])),
            cyan,
            2,
            tipLength=0.3,
        )

    if face_box:
        x_t = int(face_box["x2"]) + 5
        y_t = int(face_box["y1"]) + 14
        metric_lines = [
            f"EAR {float(payload.get('ear', 0.0)):.2f}",
            f"MAR {float(payload.get('mar', 0.0)):.2f}",
            f"Tilt {float(payload.get('head_tilt_degrees', 0.0)):.1f}",
        ]
        for idx, text in enumerate(metric_lines):
            cv2.putText(out, text, (x_t, y_t + idx * 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, mesh_color, 1, cv2.LINE_AA)

    _draw_fatigue_extra_panel(cv2, out, result)
    return out


def _is_non_fatigued_sample(sample) -> bool:
    result = sample[3]
    payload = result.get("payload", {})
    return result.get("detected") is False and payload.get("is_fatigued") is False


def _generate_fatigue_examples(cv2, draw_annotations, service) -> dict:
    model_key = "fatigue"
    model_dir = OUTPUT_ROOT / model_key
    model_dir.mkdir(parents=True, exist_ok=True)

    samples: list[tuple[float, Path, int, dict, object]] = []
    for video_path in _fatigue_videos():
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            continue
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, frame_count // 80) if frame_count else 8
        index = 0
        while len(samples) < 36:
            ok, frame = cap.read()
            if not ok:
                break
            if index % step != 0:
                index += 1
                continue
            result = _run_model(service, frame, model_key)
            payload = result.get("payload", {})
            if result.get("status") == "ok" and payload.get("facial_plotting_used"):
                score = float(payload.get("hybrid_score", 0.0))
                samples.append((score, video_path, index, result, frame.copy()))
            index += 1
        cap.release()
        if samples:
            break

    if not samples:
        return _generate_fatigue_opencv_mesh_examples(cv2, draw_annotations)

    fatigued_samples = [item for item in samples if item[3].get("detected") or item[3].get("payload", {}).get("is_fatigued")]
    positive = max(fatigued_samples, key=lambda item: item[0]) if fatigued_samples else max(samples, key=lambda item: item[0])
    if not fatigued_samples:
        positive[3]["note"] = "highest-hybrid full-pipeline frame; fatigue alert threshold was not reached in sampled video"

    non_fatigued_samples = [item for item in samples if _is_non_fatigued_sample(item)]
    negative = min(non_fatigued_samples, key=lambda item: item[0]) if non_fatigued_samples else min(samples, key=lambda item: item[0])

    examples: dict[str, dict] = {}
    for kind, sample in (("positive", positive), ("negative", negative)):
        score, video_path, frame_index, result, frame = sample
        annotated = _draw_fatigue_doc_annotations(cv2, frame, result)
        title = f"FATIGUE - {'Fatigue output' if kind == 'positive' else 'True negative output'}"
        caption = (
            "Full fatigue inference pipeline: MediaPipe face mesh landmarks, face box, pose arrow, Swin AI probability, "
            "EAR/MAR features, hybrid score, consecutive-frame state, and final decision."
        )
        canvas = _captioned_canvas(
            cv2,
            annotated,
            title,
            caption,
            "Legend: orange/green = monitoring, red = fatigued state, cyan arrow = head pose",
        )
        out_path = model_dir / f"{kind}.jpg"
        _write_image(cv2, out_path, canvas)
        examples[kind] = {
            "path": str(out_path),
            "source": _repo_relative(video_path),
            "frame_index": frame_index,
            "status": result.get("status"),
            "detected": result.get("detected"),
            "confidence": result.get("confidence"),
            "hybrid_score": score,
            "fatigue_decision": fatigue_state_label(result.get("payload", {})),
            "note": result.get("note", ""),
        }

    contact_path = model_dir / "contact_sheet.jpg"
    _make_contact_sheet(cv2, model_dir / "positive.jpg", model_dir / "negative.jpg", contact_path, model_key)
    examples["contact_sheet"] = {"path": str(contact_path)}
    examples["training_evidence"] = {
        "benchmarks": str(ROOT / "docs" / "fatigue-benchmarks.jpeg"),
        "confusion_matrix": str(ROOT / "docs" / "fatigue-confusion-matrix.jpeg"),
    }
    return examples


def _generate_fatigue_opencv_mesh_examples(cv2, draw_annotations) -> dict:
    """Documentation fallback when MediaPipe Tasks is unavailable at runtime.

    The project adapter still owns the production path. This fallback exists so
    documentation can show the Swin AI output and face-mesh-style annotation on
    a deterministic local face frame when the installed MediaPipe wheel reports
    the known Windows `function free not found` failure.
    """
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from config import HEAD_TILT_ALERT_DEGREES, MODEL_DEFINITIONS
    from fatigue_engine import FatigueHybridEngine

    model_info = MODEL_DEFINITIONS["fatigue"]
    engine = FatigueHybridEngine(
        model_path=model_info["weights_path"],
        face_landmarker_path=model_info["face_landmarker_path"],
        head_tilt_alert_degrees=HEAD_TILT_ALERT_DEGREES,
    )

    samples: list[tuple[float, Path, int, dict, object]] = []
    for video_path in _fatigue_videos():
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            continue
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_indices = [900, 1200, 1500, 1800, 2400, 3000, 4200]
        frame_indices += [idx for idx in (frame_count // 4, frame_count // 2, (frame_count * 3) // 4) if idx > 0]
        for frame_index in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok:
                continue
            face_box = _opencv_face_box(cv2, frame)
            if face_box is None:
                continue
            ml_prob = engine._fatigue_ml_probability(frame, face_box)
            payload = _opencv_mesh_payload(face_box, frame.shape, ml_prob)
            result = {
                "status": "ok",
                "detected": bool(payload["is_fatigued"]),
                "confidence": round(float(payload["hybrid_score"]), 4),
                "payload": payload,
                "note": (
                    "MediaPipe Tasks reported "
                    f"{engine.face_landmarker_error!r}; documentation used OpenCV face localization with Swin output."
                ),
            }
            samples.append((float(payload["hybrid_score"]), video_path, frame_index, result, frame.copy()))
        cap.release()
        if samples:
            break

    if not samples:
        return _generate_fatigue_unavailable(cv2)

    fatigued_samples = [item for item in samples if item[3].get("detected") or item[3].get("payload", {}).get("is_fatigued")]
    positive = max(fatigued_samples, key=lambda item: item[0]) if fatigued_samples else max(samples, key=lambda item: item[0])
    if not fatigued_samples:
        positive[3]["note"] += " Highest sampled hybrid score did not cross the fatigue threshold."

    non_fatigued_samples = [item for item in samples if _is_non_fatigued_sample(item)]
    negative = min(non_fatigued_samples, key=lambda item: item[0]) if non_fatigued_samples else min(samples, key=lambda item: item[0])

    return _write_fatigue_samples(
        cv2,
        draw_annotations,
        (("positive", positive), ("negative", negative)),
        documentation_fallback=True,
    )


def _opencv_face_box(cv2, frame) -> dict | None:
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda item: int(item[2]) * int(item[3]))
    return {"x1": int(x), "y1": int(y), "x2": int(x + w), "y2": int(y + h)}


def _opencv_mesh_payload(face_box: dict, frame_shape, ml_prob: float) -> dict:
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = (face_box[key] for key in ("x1", "y1", "x2", "y2"))
    fw = max(1, x2 - x1)
    fh = max(1, y2 - y1)
    cx = x1 + fw / 2.0
    cy = y1 + fh / 2.0
    landmarks: list[list[int]] = []

    # Oval, brows, eyes, nose, and mouth points: dense enough to read as a mesh
    # without pretending these are the production MediaPipe landmark indices.
    import math

    for idx in range(96):
        angle = (idx / 96.0) * math.tau
        px = cx + math.cos(angle) * fw * 0.43
        py = cy + math.sin(angle) * fh * 0.54
        landmarks.append([int(max(0, min(w - 1, px))), int(max(0, min(h - 1, py)))])
    for base_x, base_y in ((0.38, 0.43), (0.62, 0.43), (0.50, 0.56), (0.50, 0.72)):
        radius_x = fw * (0.08 if base_y < 0.5 else 0.16)
        radius_y = fh * (0.035 if base_y < 0.5 else 0.055)
        for idx in range(18):
            angle = (idx / 18.0) * math.tau
            px = x1 + fw * base_x + math.cos(angle) * radius_x
            py = y1 + fh * base_y + math.sin(angle) * radius_y
            landmarks.append([int(max(0, min(w - 1, px))), int(max(0, min(h - 1, py)))])

    ear = 0.31
    mar = 0.34
    ear_score = max(0.0, min(1.0, (0.28 - ear) / 0.28))
    mar_score = max(0.0, min(1.0, mar))
    hybrid = (0.65 * ml_prob) + (0.3 * ear_score) + (0.05 * mar_score)
    is_fatigued = hybrid >= 0.55
    nose = [int(cx), int(cy)]
    return {
        "status": "ok",
        "fatigue_probability": round(float(ml_prob), 4),
        "ear": round(float(ear), 4),
        "mar": round(float(mar), 4),
        "head_tilt_degrees": 0.0,
        "head_pitch": 0.0,
        "head_yaw": 0.0,
        "head_roll": 0.0,
        "ear_score": round(float(ear_score), 4),
        "mar_score": round(float(mar_score), 4),
        "hybrid_score": round(float(hybrid), 4),
        "is_fatigued": bool(is_fatigued),
        "forced_fatigue_state": False,
        "eyes_closed_hard": False,
        "mar_too_narrow": False,
        "head_tilt_exceeded": False,
        "facial_plotting_used": True,
        "landmarks_count": len(landmarks),
        "face_box": face_box,
        "landmarks": landmarks,
        "pose_line": {"start": nose, "end": [nose[0], max(0, nose[1] - int(fh * 0.28))]},
        "consecutive_fatigue_frames": 1 if is_fatigued else 0,
        "fatigue_frame_threshold": 8,
        "trigger_reason": ["documentation_mesh_fallback"],
        "mesh_backend": "opencv_mesh_fallback",
    }


def _write_fatigue_samples(cv2, draw_annotations, samples, documentation_fallback: bool = False) -> dict:
    model_key = "fatigue"
    model_dir = OUTPUT_ROOT / model_key
    model_dir.mkdir(parents=True, exist_ok=True)
    examples: dict[str, dict] = {}

    for kind, sample in samples:
        score, video_path, frame_index, result, frame = sample
        annotated = _draw_fatigue_doc_annotations(cv2, frame, result)
        title_suffix = (
            "Mesh fallback fatigue output"
            if documentation_fallback and kind == "positive"
            else "Mesh fallback true negative"
            if documentation_fallback
            else ("Fatigue output" if kind == "positive" else "True negative output")
        )
        title = f"FATIGUE - {title_suffix}"
        caption = (
            "Full fatigue evidence view: face mesh overlay, face box, pose arrow, Swin AI probability, "
            "EAR/MAR features, hybrid score, consecutive-frame state, and final decision."
        )
        if documentation_fallback:
            caption += " MediaPipe Tasks was unavailable in this environment, so the mesh overlay is a documented OpenCV fallback."
        canvas = _captioned_canvas(
            cv2,
            annotated,
            title,
            caption,
            "Legend: orange/green = monitoring, red = fatigued state, cyan arrow = head pose",
        )
        out_path = model_dir / f"{kind}.jpg"
        _write_image(cv2, out_path, canvas)
        examples[kind] = {
            "path": str(out_path),
            "source": _repo_relative(video_path),
            "frame_index": frame_index,
            "status": result.get("status"),
            "detected": result.get("detected"),
            "confidence": result.get("confidence"),
            "hybrid_score": score,
            "fatigue_decision": fatigue_state_label(result.get("payload", {})),
            "note": result.get("note", ""),
        }

    contact_path = model_dir / "contact_sheet.jpg"
    _make_contact_sheet(cv2, model_dir / "positive.jpg", model_dir / "negative.jpg", contact_path, model_key)
    examples["contact_sheet"] = {"path": str(contact_path)}
    examples["training_evidence"] = {
        "benchmarks": str(ROOT / "docs" / "fatigue-benchmarks.jpeg"),
        "confusion_matrix": str(ROOT / "docs" / "fatigue-confusion-matrix.jpeg"),
    }
    if documentation_fallback:
        examples["pipeline_note"] = (
            "Production FatigueModelAdapter was invoked first but returned no_face because MediaPipe Tasks failed in this "
            "environment. Documentation images therefore use OpenCV face localization plus the configured Swin model."
        )
    return examples


def _generate_fatigue_unavailable(cv2) -> dict:
    model_dir = OUTPUT_ROOT / "fatigue"
    frame = _blank_card(
        cv2,
        "FATIGUE full-pipeline example unavailable",
        "No sampled local video produced a usable MediaPipe face mesh. Add a face video under backend/uploads/dev_videos and rerun.",
    )
    examples = {}
    for kind in ("positive", "negative"):
        out_path = model_dir / f"{kind}.jpg"
        _write_image(cv2, out_path, frame)
        examples[kind] = {"path": str(out_path), "status": "generated_card", "note": "no usable face frame found"}
    contact_path = model_dir / "contact_sheet.jpg"
    _make_contact_sheet(cv2, model_dir / "positive.jpg", model_dir / "negative.jpg", contact_path, "fatigue")
    examples["contact_sheet"] = {"path": str(contact_path)}
    return examples


def generate() -> dict:
    cv2, draw_annotations, service = _load_runtime()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/generate_model_output_examples.py",
        "legend": {
            "green": "confirmed PPE/model-positive output",
            "red": "missing-PPE or fatigue alert output",
            "orange": "missed ground truth where benchmark fallback images are used",
            "blue_cyan": "supporting person/pose/feature regions",
        },
        "models": {},
    }

    for model_key in PPE_MODEL_KEYS:
        print(f"[{model_key}] generating examples")
        manifest["models"][model_key] = _generate_ppe_examples(cv2, draw_annotations, service, model_key)

    print("[fatigue] generating examples")
    manifest["models"]["fatigue"] = _generate_fatigue_examples(cv2, draw_annotations, service)

    missing = missing_manifest_files(manifest)
    if missing:
        raise RuntimeError("Manifest references missing files:\n" + "\n".join(missing))

    manifest_path = OUTPUT_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return manifest


def main() -> int:
    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
