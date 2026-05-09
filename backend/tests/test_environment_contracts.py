import importlib.metadata as metadata
import re
import sys


EXPECTED_MAJOR_MINOR = {
    "django": (5, 2),
    "djangorestframework": (3, 17),
    "channels": (4, 3),
    "daphne": (4, 2),
    "opencv-python-headless": (4, 13),
    "ultralytics": (8, 4),
    "torch": (2, 11),
    "torchvision": (0, 26),
    "numpy": (2, 2),
    "scipy": (1, 15),
    "pillow": (12, 2),
    "mediapipe": (0, 10),
    "pytest": (9, 0),
    "pytest-django": (4, 12),
    "pytest-timeout": (2, 4),
}

LOCAL_DEPENDENCY_PATTERNS = (
    "-e ",
    "--editable",
    "file:",
    "git+",
    "://",
    "../",
    "./",
)


def _major_minor(version):
    match = re.match(r"^(\d+)\.(\d+)", version)
    assert match is not None, f"Could not parse version: {version}"
    return int(match.group(1)), int(match.group(2))


def _manifest_lines(root_dir):
    lines = []
    for filename in ("requirements.txt", "requirements-dev.txt"):
        path = root_dir / filename
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#"):
                lines.append((filename, line.lower()))
    return lines


def test_runtime_python_version_contract():
    assert sys.version_info[:2] == (3, 10)


def test_backend_dependency_major_minor_contract():
    observed = {
        package: _major_minor(metadata.version(package))
        for package in EXPECTED_MAJOR_MINOR
    }

    assert observed == EXPECTED_MAJOR_MINOR


def test_dependency_manifests_keep_required_test_and_ml_tooling(root_dir):
    lines = [line for _, line in _manifest_lines(root_dir)]
    joined = "\n".join(lines)

    assert any(line.startswith("mediapipe") for line in lines)
    assert "dlib" not in {line.split("==", 1)[0].split(">=", 1)[0] for line in lines}
    assert any(line == "pytest" or line.startswith("pytest==") or line.startswith("pytest>=") for line in lines)
    assert any(line == "pytest-django" or line.startswith("pytest-django") for line in lines)
    assert any(line == "pytest-timeout" or line.startswith("pytest-timeout") for line in lines)
    assert "opencv-python-headless" in joined


def test_dependency_manifests_do_not_use_local_or_editable_installs(root_dir):
    offenders = [
        f"{filename}: {line}"
        for filename, line in _manifest_lines(root_dir)
        if any(pattern in line for pattern in LOCAL_DEPENDENCY_PATTERNS)
    ]

    assert offenders == []
