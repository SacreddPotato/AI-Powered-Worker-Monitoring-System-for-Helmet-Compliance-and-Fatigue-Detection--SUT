# Agent Context

## Runtime
- Use `conda activate fatigue_env` before running backend commands locally.
- For non-interactive commands, prefer `conda run -n fatigue_env <command>`.
- Run Django management commands from `backend/`, for example `python manage.py migrate`.
- `python run.py` starts Daphne (port 7860) and Vite (port 5173) together for development; production is a single Daphne process serving the built `frontend/dist/`.

## ML Models
- Model weights live in `backend/ml_models/`.
- `backend/ml_models/model_snapshot.json` pins the expected model artifacts by size, hash, and Git LFS oid.
- Regenerate the snapshot after intentional model changes with `conda run -n fatigue_env python scripts/snapshot_models.py write`.
- Verify the current checkout with `conda run -n fatigue_env python scripts/snapshot_models.py verify`.
- Always commit replaced weights together with the regenerated snapshot; the `model-snapshot` CI job fails if they diverge.
- Real ML inference regression tests are intentionally slower; mark them with `ml` and `slow`.
- `dlib` must not be reintroduced. Fatigue landmarking uses MediaPipe.

### Weight provenance (current state)
- All PPE detector weights are project-trained; none have a public download host. Distribution is Git LFS only, and the `*_MODEL_URL` environment variables are optional mirror overrides that default to empty.
- `best.pt` (helmet), `vest_detection.pt`, `gloves_detection.pt`, `goggles_detection.pt`, and `boots_detection.pt` are intentionally identical copies of one multi-class YOLOv8n fine-tuned on the Ultralytics Construction-PPE dataset (classes include helmet, gloves, vest, boots, goggles, Person, and explicit `no_*` classes). Each adapter filters its own target classes, so the shared file is functionally correct; retraining changes all five keys at once.
- `faceshield_detection.pt` is a dedicated single-class YOLOv8n trained on SH17 face-guard imagery with hard-negative mining (negatives containing faces/heads/helmets but no face guard). Face-guard is SH17's rarest class (134 labeled instances total, 110 usable for training), which bounds achievable quality.
- `safety_suit_detection.pt` is a legacy project checkpoint that produced zero correct detections on held-out labeled data; it is flagged for in-domain retraining and relies on the person-overlap fallback in the application.
- `yolov8n.pt` is the official COCO-pretrained person model (infrastructure, not a PPE detector).
- Both custom detectors were fine-tuned from official COCO-pretrained YOLOv8n with the standard Ultralytics trainer (multi-class: 40 epochs, imgsz 640, batch 16, patience 12; faceshield: 110 epochs, imgsz 640, batch 16, patience 60, `cache=ram` strongly recommended because SH17 images are large).

### Inference behavior
- `PPEModelAdapter` honors an optional per-model `inference_confidence` in `MODEL_DEFINITIONS` (default 0.35). `faceshield` runs at 0.5, tuned on the SH17 validation split for precision/recall balance.
- `HelmetModelAdapter` counts only positive helmet/hardhat classes as worn helmets; explicit absence classes (e.g. `no_helmet`) are excluded by `_is_positive_helmet_label` so they can never be miscounted as compliance.
- The explicit `no_*` classes of the multi-class model are weak (very few labeled training instances; `no_boots` produces no detections at all, making the boots key effectively a positive-presence classifier). Missing-PPE alerting therefore leans on the MediaPipe feature-region assists (gloves, goggles, boots) and the person-overlap fallback (vest, faceshield, safetysuit), which is intended behavior.

## Benchmarks
- `scripts/documentation_benchmarks/` evaluates the configured weights against independently labeled public datasets: `run_all.py` runs everything; per-model `benchmark_<key>.py` scripts exist but overwrite `summary.csv` with only their own rows, so prefer `run_all.py` (or merge against `manifest.json`) when refreshing a subset.
- Outputs land in `docs/benchmark_results/`: per-model `metrics.json`, `confusion_matrix.png`, annotated TP/FP/FN examples, plus top-level `summary.csv` and `manifest.json`.
- Datasets cache to `.benchmark_data/` (gitignored) or `BENCHMARK_DATA_DIR`. Construction-PPE (~178 MB) downloads without auth from the Ultralytics assets GitHub release. SH17 (~14 GB) downloads via the Kaggle API and needs `~/.kaggle/kaggle.json`; without credentials the SH17-based models report `dataset_unavailable` instead of failing.
- The Kaggle SH17 distribution ships no dataset YAML; the suite writes one from the official class map (`SH17_NAMES` in `common.py`, taken from the SH17 GitHub repository — note the order differs from the README's class listing).
- Matching is greedy by confidence at IoU ≥ 0.5 using each model's deployed confidence. Metrics: precision, recall, F1, and accuracy = TP/(TP+FP+FN) (critical success index; open-set detection has no true negatives, so accuracy is always ≤ F1 — accuracy = F1/(2−F1)).
- Evaluation regimes: helmet/vest/gloves/goggles/boots are measured on the Construction-PPE held-out test split and faceshield on the SH17 held-out validation split (in-domain); safetysuit is cross-dataset. Re-validate on site footage before claiming field performance.
- `BENCHMARK_MAX_IMAGES` (default 500) caps evaluated images per split; SH17 runs used 2000 to cover the full 1,620-image validation split.

## Documentation deliverable
- `docs/SafeVision_Project_Documentation.docx` is the formal bound-book project report: cover page with placeholder academic metadata (team, supervisor, course, department, discussion date — intentionally unfilled), populated table of contents with page numbers, architecture/implementation chapters, testing evidence, and appendices.
- The table of contents is pre-baked and the document also sets `w:updateFields`, so Word/LibreOffice refresh fields automatically after future edits.
- Tables are styled for print: light hairline borders, generous cell padding, repeating header rows across page breaks, and rows that do not split across pages.
- `docs/fatigue-benchmarks.jpeg` and `docs/fatigue-confusion-matrix.jpeg` are the Swin fatigue model's training evidence (~87.7% classification accuracy) and are embedded in the report's Testing and Results section.
- The report describes all PPE detectors as project-trained (true for every key; see Weight provenance above). Do not reintroduce third-party model attributions into the report or configuration.
- Git LFS tracks `*.jpeg`/`*.png` as well as weights, so report figures and benchmark images commit through LFS.

## Verification
- Run backend tests with `conda run -n fatigue_env python -m pytest`.
- Run targeted ML tests with `conda run -n fatigue_env python -m pytest -m ml`.
- Run frontend lint with `cd frontend && npm run lint`.
- Run frontend tests/build with `cd frontend && npm test -- --run && npm run build`.
- Baseline contract tests guard Python/package major-minor versions, dependency manifests, frontend tooling, CI workflow shape, and deployment automation. The environment-contract tests pass only in the pinned `fatigue_env` (Python 3.10); newer local interpreters fail them by design.
- GitHub Actions runs backend API tests, model snapshot/ML tests, frontend lint, frontend route/API tests, dependency audit reports, and the frontend build on pushes and pull requests.
- Pushes to `main` also force-sync the repository (including LFS weights) to the hosted HuggingFace Space demo via `.github/workflows/sync_to_hub.yml`.
- Dependency audits are report-only in CI; Dependabot opens weekly update PRs for GitHub Actions, Python requirements, and frontend npm dependencies.
- Ruff and Bandit are intentionally not part of the current QA workflow; do not add them unless the project policy changes.
