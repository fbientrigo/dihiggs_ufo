import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack_b/operator/build_model_derived.py"
PACK_A = ROOT / "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_model_derived", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_model_derived_overlay_is_deterministic_and_physical() -> None:
    builder = load_builder()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "first.zip"
        second = root / "second.zip"
        members = builder.patched_members(PACK_A)
        builder.write_deterministic_zip(members, first)
        builder.write_deterministic_zip(members, second)
        assert first.read_bytes() == second.read_bytes()
        builder.write_contract(root, PACK_A, first)

        point = json.loads((root / "point.json").read_text())
        assert point["point_id"] == "H2scan_mH150_tb300000"
        assert point["coupling_mode"] == "MODEL_DERIVED"
        assert point["Mh2_GeV"] == 150.0
        assert point["ctauh2_m"] == 4.32622152973311191e-03
        assert point["GHphiphi_GeV"] == -63.5914252007596588
        assert point["br_bb"] == 0.756737485808578692
        assert point["br_bb_squared"] == 0.5726516224278888
        assert point["madgraph_rerun_required"] is False
        assert point["madgraph_rerun_reason"] == "existing production card already used MH=125.13 and all other physical inputs are unchanged"
        assert point["br_bb_provenance"] == {
            "repository": "fbientrigo/dihiggs",
            "benchmark_commit": "92ad4d80f537bffd8663e42f1c6881e82849feab",
            "path": "benchmarks/FIRST_H2_RECAST_CANDIDATE.json",
            "sha256": "c8a65f1bb0c75b48b3fd0571d5e3c1ee5dcb3388222ae50d087f102a92c0af98",
            "field": "selected_candidate.br_bb",
        }
        assert "PI_FIXED" in point["forbidden_active_values"]
        assert "Mbar2_GeV2" in point["forbidden_active_values"]

        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            runtime_name = next(name for name in archive.namelist() if name.endswith("model/LLscalar_v3_UFO_runtime/"))
            parameters_path = next(name for name in archive.namelist() if name.endswith("model/LLscalar_v3_UFO_runtime/parameters.py"))
            parameters = archive.read(parameters_path).decode()
            couplings = archive.read(next(name for name in archive.namelist() if name.endswith("model/LLscalar_v3_UFO_runtime/couplings.py"))).decode()
            runtime_files = [name for name in names if name.startswith(runtime_name)]
        assert "value = 1.50000000000000000e+02" in parameters
        assert "value = 1.25130000000000000e+02" in parameters
        assert "value = 4.32622152973311191e-03" in parameters
        assert "GHphiphi" in parameters
        assert "complex(0,1)*GHphiphi" in couplings
        assert "8*complex(0,1)*Mh2**2/vev" not in couplings
        assert not any(name.endswith("py3_model.pkl") for name in names)
        assert not any("/points/" in name or "/bin/" in name or "/scripts/" in name for name in names)

        extracted = root / "runtime"
        with zipfile.ZipFile(first) as archive:
            for name in runtime_files:
                target = extracted / Path(name).relative_to(runtime_name)
                if name.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
        output = root / "written.dat"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extracted)
        subprocess.run(
            [sys.executable, "-c", "from write_param_card import write_param_card; from pathlib import Path; write_param_card(Path(__import__('sys').argv[1]))", str(output)],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        written = output.read_text()
        def card_value(name: str) -> float:
            line = next(line for line in written.splitlines() if line.endswith(f"# {name}"))
            return float(line.split()[1])

        assert math.isclose(card_value("MH"), 125.13, rel_tol=0, abs_tol=1e-12)
        assert math.isclose(card_value("Mh2"), 150.0, rel_tol=0, abs_tol=1e-12)
        assert math.isclose(card_value("ctauh2"), 4.32622152973311191e-03, rel_tol=0, abs_tol=1e-18)
        assert math.isclose(card_value("GHphiphi"), -63.5914252007596588, rel_tol=0, abs_tol=1e-12)
