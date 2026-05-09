import re


def _text(root_dir, relative):
    return (root_dir / relative).read_text(encoding="utf-8").lower()


def test_regression_workflow_prod_ready_contract(root_dir):
    workflow = _text(root_dir, ".github/workflows/backend-regression.yml")

    assert re.search(r"(?m)^\s*push:\s*$", workflow)
    assert re.search(r"(?m)^\s*pull_request:\s*$", workflow)
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "concurrency:" in workflow
    assert "timeout-minutes:" in workflow
    assert "backend-api:" in workflow
    assert "model-snapshot:" in workflow
    assert "frontend:" in workflow
    assert "dependency-audit:" in workflow
    assert "fatigue_env" in workflow
    assert 'python-version: "3.10"' in workflow
    assert 'node-version: "20"' in workflow
    assert "npm ci" in workflow
    assert "snapshot_models.py verify" in workflow
    assert 'python -m pytest -m "not ml" -q' in workflow
    assert "python -m pytest -m ml -q" in workflow
    assert "npm run lint" in workflow
    assert "npm test -- --run" in workflow
    assert "npm run build" in workflow
    assert "ruff" not in workflow
    assert "bandit" not in workflow


def test_model_cache_does_not_restore_stale_snapshots(root_dir):
    workflow = _text(root_dir, ".github/workflows/backend-regression.yml")
    model_cache = re.search(
        r"- name: cache model downloads(?P<body>.*?)- name: install python dependencies",
        workflow,
        flags=re.DOTALL,
    )

    assert model_cache is not None
    assert "hashfiles('backend/ml_models/model_snapshot.json')" in model_cache.group("body")
    assert "restore-keys" not in model_cache.group("body")


def test_dependency_audit_job_is_report_only(root_dir):
    workflow = _text(root_dir, ".github/workflows/backend-regression.yml")
    audit_job = re.search(
        r"(?ms)^  dependency-audit:(?P<body>.*?)(^  [a-z0-9_-]+:\s*$)",
        workflow + "\n  end:",
    )

    assert audit_job is not None
    body = audit_job.group("body")
    assert "continue-on-error: true" in body
    assert "pip-audit" in body
    assert "npm audit" in body
    assert "actions/upload-artifact@v4" in body


def test_huggingface_sync_workflow_contract(root_dir):
    workflow = _text(root_dir, ".github/workflows/sync_to_hub.yml")

    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "concurrency:" in workflow
    assert "actions/checkout@v4" in workflow
    assert "lfs: true" in workflow
    assert "secrets.hf_token" in workflow


def test_dependabot_contract(root_dir):
    dependabot = _text(root_dir, ".github/dependabot.yml")

    assert 'package-ecosystem: "github-actions"' in dependabot
    assert 'package-ecosystem: "pip"' in dependabot
    assert 'package-ecosystem: "npm"' in dependabot
    assert re.search(r'directory:\s*"?/"?', dependabot)
    assert re.search(r'directory:\s*"?/frontend"?', dependabot)
    assert re.search(r'interval:\s*"?weekly"?', dependabot)
