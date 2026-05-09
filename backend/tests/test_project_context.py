from pathlib import Path


def test_agents_md_documents_runtime_context(root_dir):
    text = (root_dir / "AGENTS.md").read_text(encoding="utf-8").lower()

    assert "fatigue_env" in text
    assert "conda activate fatigue_env" in text
    assert "backend/ml_models" in text
    assert "backend/" in text and "manage.py" in text
    assert "dlib" in text and "must not" in text
    assert "mediapipe" in text


def test_requirements_excludes_dlib_includes_mediapipe(root_dir):
    requirements = (root_dir / "requirements.txt").read_text(encoding="utf-8").lower().splitlines()

    normalized = [line.strip() for line in requirements if line.strip() and not line.startswith("#")]
    assert any(line.startswith("mediapipe") for line in normalized)
    assert "dlib" not in normalized


def test_code_and_tests_do_not_import_dlib(root_dir):
    scanned_paths = [
        root_dir / "backend",
        root_dir / "requirements.txt",
        root_dir / "Dockerfile",
    ]
    offenders = []
    for path in scanned_paths:
        files = [path] if path.is_file() else path.rglob("*")
        for file_path in files:
            if not file_path.is_file() or file_path.suffix.lower() not in {".py", ".txt", ".md"}:
                continue
            if file_path.parts[-2:] == ("tests", "test_project_context.py"):
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "import dlib" in text or "from dlib" in text or text.strip() == "dlib":
                offenders.append(str(file_path.relative_to(root_dir)))

    assert offenders == []


def test_public_docs_reference_mediapipe_not_dlib(root_dir):
    offenders = []
    for relative_path in ("README.md", "TECHNICAL_REPORT.md"):
        text = (root_dir / relative_path).read_text(encoding="utf-8", errors="ignore").lower()
        if "dlib" in text:
            offenders.append(relative_path)
        assert "mediapipe" in text

    assert offenders == []


def test_github_actions_runs_backend_regression_suite(root_dir):
    workflow = root_dir / ".github" / "workflows" / "backend-regression.yml"
    text = workflow.read_text(encoding="utf-8").lower()

    assert "push:" in text
    assert "pull_request:" in text
    assert "fatigue_env" in text
    assert "requirements-dev.txt" in text
    assert "snapshot_models.py verify" in text
    assert "python -m pytest -m ml -q" in text
    assert "python -m pytest -m \"not ml\" -q" in text
    assert "npm run lint" in text
    assert "npm test -- --run" in text
    assert "npm run build" in text
