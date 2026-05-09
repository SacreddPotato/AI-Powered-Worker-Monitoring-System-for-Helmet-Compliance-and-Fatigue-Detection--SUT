# Agent Context

## Runtime
- Use `conda activate fatigue_env` before running backend commands locally.
- For non-interactive commands, prefer `conda run -n fatigue_env <command>`.
- Run Django management commands from `backend/`, for example `python manage.py migrate`.

## ML Models
- Model weights live in `backend/ml_models/`.
- `backend/ml_models/model_snapshot.json` pins the expected model artifacts by size, hash, and Git LFS oid.
- Regenerate the snapshot after intentional model changes with `conda run -n fatigue_env python scripts/snapshot_models.py write`.
- Verify the current checkout with `conda run -n fatigue_env python scripts/snapshot_models.py verify`.
- Real ML inference regression tests are intentionally slower; mark them with `ml` and `slow`.
- `dlib` must not be reintroduced. Fatigue landmarking uses MediaPipe.

## Verification
- Run backend tests with `conda run -n fatigue_env python -m pytest`.
- Run targeted ML tests with `conda run -n fatigue_env python -m pytest -m ml`.
- Baseline contract tests guard Python/package major-minor versions, dependency manifests, frontend tooling, CI workflow shape, and deployment automation.
- GitHub Actions runs backend API tests, model snapshot/ML tests, frontend route/API tests, dependency audit reports, and the frontend build on pushes and pull requests.
- Dependency audits are report-only in CI; Dependabot opens weekly update PRs for GitHub Actions, Python requirements, and frontend npm dependencies.
