"""Benchmark the helmet detection YOLOv8 model.

Usage:
    python .modelStats/benchmark_helmet.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO

MODEL_PATH = ROOT / "backend" / "ml_models" / "best.pt"
RESULTS_DIR = ROOT / ".modelStats" / "helmet"


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(MODEL_PATH))

    try:
        metrics = model.val(verbose=True)
        results = {
            "mAP50": f"{metrics.box.map50:.4f}",
            "mAP50-95": f"{metrics.box.map:.4f}",
            "precision": f"{metrics.box.mp:.4f}",
            "recall": f"{metrics.box.mr:.4f}",
        }
    except Exception as e:
        print(f"model.val() failed ({e}), falling back to inference stats")
        import glob
        images = glob.glob(str(ROOT / "screenshots" / "*.png"))
        if not images:
            print("No images found for fallback evaluation.")
            results = {"error": "No validation data available"}
        else:
            all_confs = []
            for img in images:
                preds = model(img, verbose=False)
                for r in preds:
                    if r.boxes is not None and len(r.boxes):
                        all_confs.extend(r.boxes.conf.cpu().tolist())
            results = {
                "images_tested": len(images),
                "total_detections": len(all_confs),
                "mean_confidence": f"{sum(all_confs)/len(all_confs):.4f}" if all_confs else "N/A",
            }

    out_file = RESULTS_DIR / "results.txt"
    with open(out_file, "w") as f:
        for k, v in results.items():
            f.write(f"{k}: {v}\n")
            print(f"{k}: {v}")

    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
