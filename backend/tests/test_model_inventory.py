import re

from conftest import EXPECTED_MODEL_KEYS


def _quoted_strings(text):
    return set(re.findall(r"['\"]([a-z][a-z0-9_]+)['\"]", text))


def test_model_definitions_include_expected_inventory():
    from config import MODEL_DEFINITIONS

    assert tuple(MODEL_DEFINITIONS.keys()) == EXPECTED_MODEL_KEYS


def test_django_seed_migrations_include_expected_inventory(root_dir):
    migration_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root_dir / "backend" / "detection" / "migrations").glob("000*_seed*.py")
    )

    assert EXPECTED_MODEL_KEYS == tuple(key for key in EXPECTED_MODEL_KEYS if key in _quoted_strings(migration_text))


def test_annotation_supports_every_model_key(root_dir):
    annotation_text = (root_dir / "backend" / "annotation.py").read_text(encoding="utf-8")
    keys = _quoted_strings(annotation_text)

    assert set(EXPECTED_MODEL_KEYS).issubset(keys)


def test_devlab_frontend_model_inventory_matches_backend(root_dir):
    devlab_text = (root_dir / "frontend" / "src" / "pages" / "DevLabPage.jsx").read_text(encoding="utf-8")
    declared = re.search(r"ALL_MODELS\s*=\s*\[([^\]]+)\]", devlab_text)
    assert declared is not None

    keys = tuple(re.findall(r'"([^"]+)"', declared.group(1)))
    assert keys == EXPECTED_MODEL_KEYS
