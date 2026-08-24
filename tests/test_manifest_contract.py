from __future__ import annotations

import json
from pathlib import Path


def test_manifest_has_expected_domain():
    manifest = json.loads(Path("custom_components/orphan_cleaner/manifest.json").read_text())
    assert manifest["domain"] == "orphan_cleaner"
    assert manifest["version"] == "1.0.4"
