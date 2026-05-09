import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
SNAPSHOT_PATH = BACKEND_DIR / "ml_models" / "model_snapshot.json"
ARTIFACT_FIELDS = ("weights_path", "person_model_path", "face_landmarker_path")


def _load_model_definitions():
    sys.path.insert(0, str(BACKEND_DIR))
    from config import MODEL_DEFINITIONS

    return MODEL_DEFINITIONS


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_lfs_oids():
    try:
        result = subprocess.run(
            ["git", "lfs", "ls-files", "-l"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return {}

    if result.returncode != 0:
        return {}

    out = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            out[parts[-1].replace("\\", "/")] = parts[0]
    return out


def _configured_artifacts():
    refs = defaultdict(list)
    for model_key, definition in _load_model_definitions().items():
        for field in ARTIFACT_FIELDS:
            raw_path = definition.get(field)
            if not raw_path:
                continue
            path = Path(raw_path).resolve()
            relative = path.relative_to(ROOT).as_posix()
            refs[relative].append({"model_key": model_key, "field": field})
    return refs


def build_snapshot():
    refs = _configured_artifacts()
    lfs_oids = _git_lfs_oids()
    artifacts = []
    missing = []

    for relative in sorted(refs):
        path = ROOT / relative
        if not path.exists():
            missing.append(relative)
            continue
        artifact = {
            "path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "model_key_refs": sorted(refs[relative], key=lambda item: (item["model_key"], item["field"])),
        }
        if relative in lfs_oids:
            artifact["lfs_oid"] = lfs_oids[relative]
        artifacts.append(artifact)

    if missing:
        raise SystemExit("Missing model artifacts:\n" + "\n".join(f"- {item}" for item in missing))

    return {
        "schema_version": 1,
        "generated_by": "scripts/snapshot_models.py",
        "artifacts": artifacts,
    }


def write_snapshot():
    snapshot = build_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {SNAPSHOT_PATH.relative_to(ROOT).as_posix()} with {len(snapshot['artifacts'])} artifacts")


def verify_snapshot():
    if not SNAPSHOT_PATH.exists():
        raise SystemExit(f"Snapshot missing: {SNAPSHOT_PATH.relative_to(ROOT).as_posix()}")

    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = build_snapshot()
    if actual != expected:
        print("Model snapshot mismatch. Regenerate with:", file=sys.stderr)
        print("  conda run -n fatigue_env python scripts/snapshot_models.py write", file=sys.stderr)
        raise SystemExit(1)

    print(f"Snapshot verified: {len(actual['artifacts'])} artifacts")


def main():
    parser = argparse.ArgumentParser(description="Write or verify the model artifact snapshot.")
    parser.add_argument("mode", choices=("write", "verify"))
    args = parser.parse_args()

    if args.mode == "write":
        write_snapshot()
    else:
        verify_snapshot()


if __name__ == "__main__":
    main()
