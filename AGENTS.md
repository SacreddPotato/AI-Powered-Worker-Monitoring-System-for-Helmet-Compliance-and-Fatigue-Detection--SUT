# Agent Context

## Runtime
- Use `conda activate fatigue_env` before running backend commands locally.
- For non-interactive commands, prefer `conda run -n fatigue_env <command>`.
- Run Django management commands from `backend/`, for example `python manage.py migrate`.

## ML Models
- Model weights live in `backend/ml_models/`.
- Real ML inference regression tests are intentionally slower; mark them with `ml` and `slow`.
- `dlib` must not be reintroduced. Fatigue landmarking uses MediaPipe.

## Verification
- Run backend tests with `conda run -n fatigue_env python -m pytest`.
- Run targeted ML tests with `conda run -n fatigue_env python -m pytest -m ml`.
- GitHub Actions runs the same pytest suite on pushes and pull requests. The workflow can download the fatigue model only when `FATIGUE_MODEL_URL` is configured as a repository secret or environment variable.
