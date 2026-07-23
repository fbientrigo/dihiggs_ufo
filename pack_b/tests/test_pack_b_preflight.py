#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pack_b/operator/config.json"
PREFLIGHT = ROOT / "pack_b/operator/pack_b_preflight.py"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manifest = Path(tmp) / "manifest.json"
        passed = subprocess.run([sys.executable, str(PREFLIGHT), str(CONFIG), "--manifest", str(manifest)], check=False, capture_output=True, text=True)
        assert passed.returncode == 0, passed.stderr + passed.stdout
        assert json.loads(manifest.read_text())["status"] == "PASS"

        invalid = Path(tmp) / "invalid.json"
        data = json.loads(CONFIG.read_text())
        data["output_dir"] = "/tmp/pack-b-invalid"
        invalid.write_text(json.dumps(data))
        failed = subprocess.run([sys.executable, str(PREFLIGHT), str(invalid)], check=False, capture_output=True, text=True)
        assert failed.returncode == 1
        assert "output_dir" in failed.stdout


def test_pack_b_preflight() -> None:
    main()


if __name__ == "__main__":
    main()

