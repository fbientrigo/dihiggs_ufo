import importlib.util
import json
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
        assert "PI_FIXED" in point["forbidden_active_values"]
        assert "Mbar2_GeV2" in point["forbidden_active_values"]

        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            parameters = archive.read(next(name for name in archive.namelist() if name.endswith("model/LLscalar_v3_UFO_runtime/parameters.py"))).decode()
            couplings = archive.read(next(name for name in archive.namelist() if name.endswith("model/LLscalar_v3_UFO_runtime/couplings.py"))).decode()
        assert "value = 1.50000000000000000e+02" in parameters
        assert "value = 4.32622152973311191e-03" in parameters
        assert "GHphiphi" in parameters
        assert "complex(0,1)*GHphiphi" in couplings
        assert "8*complex(0,1)*Mh2**2/vev" not in couplings
        assert not any(name.endswith("py3_model.pkl") for name in names)
        assert not any("/points/" in name or "/bin/" in name or "/scripts/" in name for name in names)
