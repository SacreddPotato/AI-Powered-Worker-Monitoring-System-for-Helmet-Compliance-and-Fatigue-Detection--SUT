"""Shared utilities for documentation benchmarks.

Evaluates the project's PPE detection weights against real labeled datasets
(detection-level metrics: precision / recall / F1 via IoU matching).

Datasets:
- Ultralytics Construction-PPE (no-auth download from GitHub releases)
- SH17 (Kaggle, requires ~/.kaggle/kaggle.json; used only for faceshield and
  safetysuit, which have no ground truth in Construction-PPE)

Outputs land in docs/benchmark_results/<model_key>/ plus a top-level
summary.csv and manifest.json.

Usage:
    python scripts/documentation_benchmarks/run_all.py
    python scripts/documentation_benchmarks/benchmark_helmet.py
Optional env:
    BENCHMARK_DATA_DIR  dataset cache directory (default: <repo>/.benchmark_data)
    BENCHMARK_MAX_IMAGES  cap on evaluated images per dataset split (default 500)
"""

import json
import os
import random
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
ML_MODELS_DIR = ROOT / "backend" / "ml_models"
RESULTS_DIR = ROOT / "docs" / "benchmark_results"
DATA_DIR = Path(os.environ.get("BENCHMARK_DATA_DIR", ROOT / ".benchmark_data"))
MAX_IMAGES = int(os.environ.get("BENCHMARK_MAX_IMAGES", "500"))

CONSTRUCTION_PPE_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip"
SH17_KAGGLE_REF = "mugheesahmad/sh17-dataset-for-ppe-detection"

IOU_THRESHOLD = 0.5
# Match the confidence used by the application's inference adapters.
CONF_THRESHOLD = 0.35
MAX_EXAMPLE_IMAGES = 6


def _normalize(name: str) -> str:
    return str(name).lower().replace("_", " ").replace("-", " ").strip()


@dataclass
class ClassSpec:
    canonical: str
    gt_names: List[str]
    pred_names: List[str]

    def matches_gt(self, name: str) -> bool:
        return _normalize(name) in {_normalize(n) for n in self.gt_names}

    def matches_pred(self, name: str) -> bool:
        return _normalize(name) in {_normalize(n) for n in self.pred_names}


@dataclass
class BenchmarkSpec:
    model_key: str
    weights: Path
    dataset: str  # "construction-ppe" or "sh17"
    classes: List[ClassSpec]
    conf: float = CONF_THRESHOLD
    notes: str = ""


# ---------------------------------------------------------------- datasets


def ensure_construction_ppe() -> Optional[Path]:
    """Download/extract the Ultralytics Construction-PPE dataset. Returns root dir."""
    root = DATA_DIR / "construction-ppe"
    if (root / "data.yaml").exists():
        return root
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "construction-ppe.zip"
    if not zip_path.exists():
        print(f"Downloading Construction-PPE from {CONSTRUCTION_PPE_URL} ...")
        urllib.request.urlretrieve(CONSTRUCTION_PPE_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        top = names[0].split("/")[0] if names and "/" in names[0] else None
        zf.extractall(DATA_DIR / "_construction_ppe_tmp")
    extracted = DATA_DIR / "_construction_ppe_tmp"
    candidates = list(extracted.rglob("data.yaml"))
    if not candidates:
        raise RuntimeError("Construction-PPE archive missing data.yaml")
    shutil.move(str(candidates[0].parent), str(root))
    shutil.rmtree(extracted, ignore_errors=True)
    return root


# Official SH17 class map (https://github.com/ahmadmughees/SH17dataset, sh17.yaml).
# The Kaggle distribution ships images/ + labels/ + split lists but no YAML.
SH17_NAMES = {
    0: "person", 1: "ear", 2: "ear-mufs", 3: "face", 4: "face-guard",
    5: "face-mask", 6: "foot", 7: "tool", 8: "glasses", 9: "gloves",
    10: "helmet", 11: "hands", 12: "head", 13: "medical-suit", 14: "shoes",
    15: "safety-suit", 16: "safety-vest",
}


def _write_sh17_yaml(root: Path) -> None:
    yaml_path = root / "data.yaml"
    if yaml_path.exists():
        return
    lines = ["# Generated from the official SH17 class map (sh17.yaml on GitHub).", "names:"]
    lines += [f"  {idx}: {name}" for idx, name in SH17_NAMES.items()]
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_sh17() -> Optional[Path]:
    """Download/extract SH17 via the Kaggle API if credentials are available.

    Returns the dataset root, or None when unavailable (no credentials /
    download failure). Callers must degrade gracefully — this dataset is the
    only labeled ground truth source for faceshield and safetysuit.
    """
    root = DATA_DIR / "sh17"
    if (root / "labels").is_dir() and (root / "val_files.txt").exists():
        _write_sh17_yaml(root)
        return root
    kaggle_creds = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_creds.exists() and not os.environ.get("KAGGLE_USERNAME"):
        print("SH17: no Kaggle credentials; skipping download.")
        return None
    root.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [sys.executable, "-m", "kaggle", "datasets", "download", "-d", SH17_KAGGLE_REF, "-p", str(root)],
            check=True,
        )
        archive = next(root.glob("*.zip"))
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(root)
        archive.unlink()
    except Exception as exc:  # noqa: BLE001 — degrade to "not benchmarked"
        print(f"SH17 download failed: {exc}")
        return None
    _write_sh17_yaml(root)
    return root


def _parse_yaml_names(yaml_path: Path) -> Dict[int, str]:
    """Tiny YAML class-map parser (avoids a PyYAML dependency)."""
    names: Dict[int, str] = {}
    in_names = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        if stripped.strip() == "names:":
            in_names = True
            continue
        if in_names:
            if not stripped.startswith((" ", "\t")):
                break
            if ":" in stripped:
                key, value = stripped.strip().split(":", 1)
                try:
                    names[int(key)] = value.strip().strip("'\"")
                except ValueError:
                    break
    return names


def dataset_images_and_labels(dataset_root: Path, split_preference: Tuple[str, ...] = ("test", "val", "valid")) -> Tuple[List[Path], Path, Dict[int, str], str]:
    """Locate an evaluation split. Returns (images, labels_dir, class_names, split_name)."""
    yaml_candidates = sorted(dataset_root.glob("*.yaml")) + sorted(dataset_root.glob("*.yml"))
    names: Dict[int, str] = {}
    for candidate in yaml_candidates:
        names = _parse_yaml_names(candidate)
        if names:
            break
    if not names:
        raise RuntimeError(f"No class names found under {dataset_root}")

    # Flat layout with split list files (SH17 style): images/, labels/, val_files.txt
    val_list = dataset_root / "val_files.txt"
    if val_list.exists() and (dataset_root / "labels").is_dir():
        images = []
        for line in val_list.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            candidate = dataset_root / line
            if not candidate.exists():
                candidate = dataset_root / "images" / Path(line).name
            if candidate.exists():
                images.append(candidate)
        if images:
            return sorted(images), dataset_root / "labels", names, "val"

    for split in split_preference:
        img_dir = None
        for candidate in (dataset_root / "images" / split, dataset_root / split / "images"):
            if candidate.is_dir():
                img_dir = candidate
                break
        if img_dir is None:
            continue
        if img_dir.parent.name == "images":
            lbl_dir = dataset_root / "labels" / split
        else:
            lbl_dir = img_dir.parent / "labels"
        if not lbl_dir.is_dir():
            continue
        images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
        if images:
            return images, lbl_dir, names, split
    raise RuntimeError(f"No usable split with labels found under {dataset_root}")


def load_yolo_labels(label_path: Path, width: int, height: int) -> List[Tuple[int, Tuple[float, float, float, float]]]:
    boxes = []
    if not label_path.exists():
        return boxes
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        cls_id = int(float(parts[0]))
        cx, cy, w, h = (float(v) for v in parts[1:5])
        x1 = (cx - w / 2) * width
        y1 = (cy - h / 2) * height
        x2 = (cx + w / 2) * width
        y2 = (cy + h / 2) * height
        boxes.append((cls_id, (x1, y1, x2, y2)))
    return boxes


# ---------------------------------------------------------------- evaluation


def iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / max(area_a + area_b - inter, 1e-9)


def run_benchmark(spec: BenchmarkSpec) -> Dict:
    """Run a detection benchmark for one model spec. Writes per-model outputs."""
    import cv2
    from ultralytics import YOLO

    out_dir = RESULTS_DIR / spec.model_key
    out_dir.mkdir(parents=True, exist_ok=True)

    result: Dict = {
        "model_key": spec.model_key,
        "weights": str(spec.weights.relative_to(ROOT)) if spec.weights.is_relative_to(ROOT) else str(spec.weights),
        "dataset": spec.dataset,
        "iou_threshold": IOU_THRESHOLD,
        "conf_threshold": spec.conf,
        "notes": spec.notes,
    }

    if not spec.weights.exists():
        result["status"] = "weights_missing"
        (out_dir / "metrics.json").write_text(json.dumps(result, indent=2))
        return result

    model = YOLO(str(spec.weights))
    result["model_classes"] = {int(k): v for k, v in (model.names or {}).items()}
    if getattr(model, "task", "detect") != "detect":
        result["status"] = "incompatible_weights"
        result["detail"] = (
            f"Configured weights are a YOLOv8 '{model.task}' checkpoint and cannot produce "
            "bounding boxes; detection-level benchmarking is not possible with these weights."
        )
        (out_dir / "metrics.json").write_text(json.dumps(result, indent=2))
        print(f"[{spec.model_key}] SKIPPED: {result['detail']}")
        return result

    if spec.dataset == "construction-ppe":
        dataset_root = ensure_construction_ppe()
    else:
        dataset_root = ensure_sh17()
    if dataset_root is None:
        result["status"] = "dataset_unavailable"
        (out_dir / "metrics.json").write_text(json.dumps(result, indent=2))
        return result

    images, labels_dir, dataset_names, split = dataset_images_and_labels(dataset_root)
    if len(images) > MAX_IMAGES:
        rng = random.Random(0)
        images = sorted(rng.sample(images, MAX_IMAGES))
    result["split"] = split
    result["images_evaluated"] = len(images)
    result["dataset_classes"] = dataset_names

    gt_class_ids: Dict[str, set] = {
        cs.canonical: {cid for cid, name in dataset_names.items() if cs.matches_gt(name)}
        for cs in spec.classes
    }
    result["gt_class_ids"] = {k: sorted(v) for k, v in gt_class_ids.items()}

    per_class = {
        cs.canonical: {"tp": 0, "fp": 0, "fn": 0, "n_gt": 0, "n_pred": 0, "confidences": []}
        for cs in spec.classes
    }
    examples: List[Tuple[float, Path, List[Dict]]] = []

    for image_path in images:
        frame = cv2.imread(str(image_path))
        if frame is None:
            continue
        height, width = frame.shape[:2]
        gt_boxes = load_yolo_labels(labels_dir / (image_path.stem + ".txt"), width, height)
        prediction = model(frame, conf=spec.conf, verbose=False)[0]
        pred_items = []
        for box in prediction.boxes:
            name = model.names.get(int(box.cls[0]), "")
            pred_items.append((name, float(box.conf[0]), tuple(float(v) for v in box.xyxy[0])))

        image_overlays: List[Dict] = []
        image_interest = 0.0
        for cs in spec.classes:
            gts = [b for cid, b in gt_boxes if cid in gt_class_ids[cs.canonical]]
            preds = sorted(
                [(c, b) for n, c, b in pred_items if cs.matches_pred(n)],
                key=lambda item: -item[0],
            )
            stats = per_class[cs.canonical]
            stats["n_gt"] += len(gts)
            stats["n_pred"] += len(preds)
            matched_gt = set()
            for conf, pbox in preds:
                best_iou, best_idx = 0.0, -1
                for idx, gbox in enumerate(gts):
                    if idx in matched_gt:
                        continue
                    overlap = iou(pbox, gbox)
                    if overlap > best_iou:
                        best_iou, best_idx = overlap, idx
                if best_iou >= IOU_THRESHOLD:
                    matched_gt.add(best_idx)
                    stats["tp"] += 1
                    stats["confidences"].append(conf)
                    image_overlays.append({"box": pbox, "kind": "tp", "label": f"{cs.canonical} {conf:.2f}"})
                else:
                    stats["fp"] += 1
                    image_interest += 1
                    image_overlays.append({"box": pbox, "kind": "fp", "label": f"FP {cs.canonical} {conf:.2f}"})
            for idx, gbox in enumerate(gts):
                if idx not in matched_gt:
                    stats["fn"] += 1
                    image_interest += 1
                    image_overlays.append({"box": gbox, "kind": "fn", "label": f"missed {cs.canonical}"})
        if image_overlays:
            image_interest += 0.1
            examples.append((image_interest, image_path, image_overlays))

    summary = {}
    for canonical, stats in per_class.items():
        tp, fp, fn = stats["tp"], stats["fp"], stats["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        # Detection accuracy (no true negatives exist in open-set detection):
        # TP / (TP + FP + FN), a.k.a. the critical success index / Jaccard index.
        accuracy = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
        summary[canonical] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "n_gt": stats["n_gt"],
            "n_pred": stats["n_pred"],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "accuracy": round(accuracy, 4),
            "mean_tp_confidence": round(sum(stats["confidences"]) / len(stats["confidences"]), 4)
            if stats["confidences"]
            else None,
        }
    result["status"] = "ok"
    result["per_class"] = summary

    _plot_confusion(spec, summary, out_dir)
    _save_examples(spec, examples, out_dir)
    (out_dir / "metrics.json").write_text(json.dumps(result, indent=2))
    print(f"[{spec.model_key}] done: " + ", ".join(f"{k} F1={v['f1']}" for k, v in summary.items()))
    return result


def _plot_confusion(spec: BenchmarkSpec, summary: Dict, out_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = list(summary.keys())
    n = len(labels)
    matrix = np.zeros((n + 1, n + 1))
    for i, canonical in enumerate(labels):
        stats = summary[canonical]
        matrix[i, i] = stats["tp"]
        matrix[i, n] = stats["fp"]   # predicted class vs background (false positives)
        matrix[n, i] = stats["fn"]   # background predicted vs actual class (misses)
    fig, ax = plt.subplots(figsize=(1.8 * (n + 1) + 2.4, 1.6 * (n + 1) + 1.8))
    im = ax.imshow(matrix, cmap="Blues")
    tick_labels = labels + ["background"]
    ax.set_xticks(range(n + 1), tick_labels, rotation=30, ha="right")
    ax.set_yticks(range(n + 1), tick_labels)
    ax.set_xlabel("Ground truth")
    ax.set_ylabel("Predicted")
    ax.set_title(f"Confusion Matrix — {spec.model_key} ({spec.dataset}, IoU≥{IOU_THRESHOLD}, conf≥{spec.conf})")
    for i in range(n + 1):
        for j in range(n + 1):
            ax.text(j, i, int(matrix[i, j]), ha="center", va="center",
                    color="white" if matrix[i, j] > matrix.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_matrix.png", dpi=160)
    plt.close(fig)


def _save_examples(spec: BenchmarkSpec, examples, out_dir: Path) -> None:
    import cv2

    colors = {"tp": (80, 200, 0), "fp": (0, 0, 230), "fn": (0, 140, 255)}
    examples_dir = out_dir / "examples"
    examples_dir.mkdir(exist_ok=True)
    for old in examples_dir.glob("*.jpg"):
        old.unlink()
    examples.sort(key=lambda item: -item[0])
    for _, image_path, overlays in examples[:MAX_EXAMPLE_IMAGES]:
        frame = cv2.imread(str(image_path))
        if frame is None:
            continue
        for overlay in overlays:
            x1, y1, x2, y2 = (int(v) for v in overlay["box"])
            color = colors[overlay["kind"]]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, overlay["label"], (x1, max(14, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.imwrite(str(examples_dir / f"{image_path.stem}.jpg"), frame)


def write_summary(results: List[Dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = ["model_key,dataset,split,class,tp,fp,fn,precision,recall,f1,accuracy,status"]
    for result in results:
        if result.get("per_class"):
            for canonical, stats in result["per_class"].items():
                rows.append(
                    f"{result['model_key']},{result['dataset']},{result.get('split','')},{canonical},"
                    f"{stats['tp']},{stats['fp']},{stats['fn']},"
                    f"{stats['precision']},{stats['recall']},{stats['f1']},{stats['accuracy']},{result['status']}"
                )
        else:
            rows.append(f"{result['model_key']},{result['dataset']},,,,,,,,,,{result['status']}")
    (RESULTS_DIR / "summary.csv").write_text("\n".join(rows) + "\n")

    manifest = {
        "generated_by": "scripts/documentation_benchmarks/run_all.py",
        "iou_threshold": IOU_THRESHOLD,
        "datasets": {
            "construction-ppe": {
                "source": CONSTRUCTION_PPE_URL,
                "license": "AGPL-3.0 (Ultralytics Construction-PPE)",
            },
            "sh17": {
                "source": f"kaggle:{SH17_KAGGLE_REF}",
                "license": "CC BY-NC-SA 4.0 (research/non-commercial; see dataset page)",
            },
        },
        "results": results,
    }
    (RESULTS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {RESULTS_DIR / 'summary.csv'} and manifest.json")
