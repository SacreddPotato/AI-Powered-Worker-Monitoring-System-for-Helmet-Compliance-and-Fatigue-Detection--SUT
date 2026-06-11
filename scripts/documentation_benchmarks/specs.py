"""Benchmark specs for each PPE detection model key.

Each spec maps the application's configured weights to the labeled dataset
classes used as ground truth. Fatigue is not listed here: its evidence comes
from the dedicated Swin Transformer training benchmark
(docs/fatigue-benchmarks.jpeg, docs/fatigue-confusion-matrix.jpeg).

Evaluation regimes (called out in the report):
- helmet, vest, gloves, goggles, boots: project-trained detector vs the
  Construction-PPE held-out test split (in-domain)
- faceshield: project-trained detector vs the SH17 held-out validation split
- safetysuit: project checkpoint vs SH17 validation split (cross-dataset)
"""

from common import BenchmarkSpec, ClassSpec, ML_MODELS_DIR

SPECS = {
    "helmet": BenchmarkSpec(
        model_key="helmet",
        weights=ML_MODELS_DIR / "best.pt",
        dataset="construction-ppe",
        classes=[
            ClassSpec("helmet", gt_names=["helmet"], pred_names=["helmet", "hardhat"]),
            ClassSpec("no_helmet", gt_names=["no_helmet"], pred_names=["no_helmet", "no hardhat"]),
        ],
        notes="Project-trained helmet detector vs Construction-PPE held-out test split (in-domain).",
    ),
    "vest": BenchmarkSpec(
        model_key="vest",
        weights=ML_MODELS_DIR / "vest_detection.pt",
        dataset="construction-ppe",
        classes=[ClassSpec("vest", gt_names=["vest"], pred_names=["vest", "safety_vest", "Safety Vest"])],
        notes="Project-trained vest detector vs Construction-PPE held-out test split (in-domain).",
    ),
    "gloves": BenchmarkSpec(
        model_key="gloves",
        weights=ML_MODELS_DIR / "gloves_detection.pt",
        dataset="construction-ppe",
        classes=[
            ClassSpec("gloves", gt_names=["gloves"], pred_names=["gloves", "glove"]),
            ClassSpec("no_gloves", gt_names=["no_gloves"], pred_names=["no_gloves", "no_glove"]),
        ],
        notes="Project-trained gloves detector vs Construction-PPE held-out test split (in-domain).",
    ),
    "goggles": BenchmarkSpec(
        model_key="goggles",
        weights=ML_MODELS_DIR / "goggles_detection.pt",
        dataset="construction-ppe",
        classes=[
            ClassSpec("goggles", gt_names=["goggles"], pred_names=["goggles", "goggle"]),
            ClassSpec("no_goggle", gt_names=["no_goggle"], pred_names=["no_goggle", "no_goggles"]),
        ],
        notes="Project-trained goggles detector vs Construction-PPE held-out test split (in-domain).",
    ),
    "boots": BenchmarkSpec(
        model_key="boots",
        weights=ML_MODELS_DIR / "boots_detection.pt",
        dataset="construction-ppe",
        classes=[
            ClassSpec("boots", gt_names=["boots"], pred_names=["boots", "boot"]),
            ClassSpec("no_boots", gt_names=["no_boots"], pred_names=["no_boots", "no_boot"]),
        ],
        notes="Project-trained boots detector vs Construction-PPE held-out test split (in-domain).",
    ),
    "faceshield": BenchmarkSpec(
        model_key="faceshield",
        weights=ML_MODELS_DIR / "faceshield_detection.pt",
        dataset="sh17",
        classes=[ClassSpec("faceshield", gt_names=["face-guard", "face guard", "faceguard"], pred_names=["faceshield", "face shield", "Face Shield"])],
        conf=0.5,  # matches the model's configured inference_confidence
        notes="Project-trained face-shield detector vs SH17 held-out validation split (in-domain).",
    ),
    "safetysuit": BenchmarkSpec(
        model_key="safetysuit",
        weights=ML_MODELS_DIR / "safety_suit_detection.pt",
        dataset="sh17",
        classes=[ClassSpec("safetysuit", gt_names=["safety-suit", "safety suit"], pred_names=["safety_suit", "safety suit"])],
        notes="Safety suit weights vs SH17 'safety-suit' class (Kaggle; skipped when unavailable).",
    ),
}
