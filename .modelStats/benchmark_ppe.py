"""Benchmark the PPE detection YOLOv8 models (vest, gloves, goggles).

Usage:
    python .modelStats/benchmark_ppe.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO

MODELS = {
    "vest": ROOT / "backend" / "ml_models" / "vest_detection.pt",
    "gloves": ROOT / "backend" / "ml_models" / "gloves_detection.pt",
    "goggles": ROOT / "backend" / "ml_models" / "goggles_detection.pt",
}
RESULTS_DIR = ROOT / ".modelStats" / "ppe"


def benchmark_model(name, model_path):
    print(f"\n{'='*40}")
    print(f"Benchmarking: {name}")
    print(f"{'='*40}")
    model = YOLO(str(model_path))

    try:
        metrics = model.val(verbose=True)
        return {
            f"{name}_mAP50": f"{metrics.box.map50:.4f}",
            f"{name}_mAP50-95": f"{metrics.box.map:.4f}",
            f"{name}_precision": f"{metrics.box.mp:.4f}",
            f"{name}_recall": f"{metrics.box.mr:.4f}",
        }
    except Exception as e:
        print(f"model.val() failed for {name}: {e}")
        return {f"{name}_error": str(e)}


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {}

    for name, path in MODELS.items():
        if not path.exists():
            print(f"Skipping {name} — weight file not found at {path}")
            all_results[f"{name}_error"] = "weight file missing"
            continue
        all_results.update(benchmark_model(name, path))

    out_file = RESULTS_DIR / "results.txt"
    with open(out_file, "w") as f:
        for k, v in all_results.items():
            f.write(f"{k}: {v}\n")
            print(f"{k}: {v}")

    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
