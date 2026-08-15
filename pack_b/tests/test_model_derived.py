import importlib.util
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SCRIPT = ROOT / "pack_b/operator/build_model_derived.py"
PACK_A = ROOT / "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"

# Exact decimal-text inputs that reproduce the historical anchor's hardcoded
# constants byte-for-byte through build_model_derived's Decimal-based
# formatter. See build_model_derived.py's module docstring for why these
# must be passed as exact decimal strings, not Python floats.
HISTORICAL_MANIFEST = {
    "point_id": "H2scan_mH150_tb300000",
    "model_variant": "FACTORIZED_G_ONLY",
    "m_h_GeV": "125.13",
    "m_H2_GeV": "150.0",
    "g_hH2H2_GeV": "-63.5914252007596588",
    "total_width_GeV": "4.56118529862185007e-14",
    "ctau_physical_mm": "4.32622152973311191",
    "ctau_response_mm": "4.32622152973311191",
    "lifetime_mode": "PHYSICAL_PREDICTION",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    # Register before exec: build_model_derived.py uses @dataclass, whose
    # decorator resolves annotations via sys.modules[cls.__module__] at
    # class-definition time, which requires the module to already be
    # registered under its own name.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_new():
    return load_module(CANONICAL_SCRIPT, "canonical_builder")


def test_historical_anchor_regression_byte_identical() -> None:
    """The mandatory closure proof: feeding the historical 150 GeV anchor's
    exact values through the new generic path must reproduce the same
    patched UFO member bytes as the old hardcoded path, for every member."""
    new = load_new()

    point = new.validate_point_manifest(HISTORICAL_MANIFEST)
    new_members = new.patched_members(PACK_A, point)

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "anchor.zip"
        new.write_deterministic_zip(new_members, archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == (
            "9c685714f8840190cb08c34e4b804481564599619c1a3fa9a212256624951d33"
        )


def test_historical_anchor_regression_zip_byte_identical() -> None:
    """Same as above, but through the full write_deterministic_zip path,
    so the deterministic-zip metadata (mtimes, external_attr, ordering) is
    covered too, not just the patched member bytes."""
    new = load_new()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        point = new.validate_point_manifest(HISTORICAL_MANIFEST)
        new_dir = new.build_point(PACK_A, point, root / "new_out")
        new_zip = new_dir / "ufo_overlay.zip"

        assert hashlib.sha256(new_zip.read_bytes()).hexdigest() == (
            "9c685714f8840190cb08c34e4b804481564599619c1a3fa9a212256624951d33"
        )


def test_different_point_produces_correctly_patched_values() -> None:
    new = load_new()
    manifest = {
        "point_id": "P_test_400",
        "model_variant": "FACTORIZED_G_ONLY",
        "m_h_GeV": "125.13",
        "m_H2_GeV": "400.0",
        "g_hH2H2_GeV": "12.5",
        "total_width_GeV": "4.56118529862185007e-14",
        "ctau_physical_mm": "4.32622152973311191",
        "ctau_response_mm": "50.0",
        "lifetime_mode": "DETECTOR_RESPONSE_EXPERIMENT",
    }
    point = new.validate_point_manifest(manifest)
    members = new.patched_members(PACK_A, point)
    param_name = next(n for n in members if n.endswith("parameters.py"))
    text = members[param_name].decode()
    assert "4.00000000000000000e+02" in text  # Mh2
    assert "1.25000000000000000e+01" in text  # GHphiphi (direct convention, no sign flip)
    # default mediator mass (125.13) and ctau placeholder must still be patched in
    assert "1.25130000000000000e+02" in text
    # no historical-anchor-only values leaked into this different point's output
    assert "1.50000000000000000e+02" not in text
    assert "-6.35914252007596588e+01" not in text and "6.35914252007596588e+01" not in text


def test_no_hardcoded_historical_values_in_generic_module_code() -> None:
    """No hardcoded 150 GeV / historical coupling / historical ctau / historical
    BR may remain in the generic module's *executable code* (the module
    docstring legitimately names/quotes these values in prose, comparing
    against the historical script by design -- this test strips the leading
    module docstring before checking, so only code is scanned)."""
    import ast

    text = CANONICAL_SCRIPT.read_text()
    tree = ast.parse(text)
    docstring = ast.get_docstring(tree) or ""
    code_only = text.replace(docstring, "", 1)

    assert "150.0" not in code_only
    assert "H2scan_mH150_tb300000" not in code_only
    assert "63.5914252007596588" not in code_only
    assert "4.32622152973311191" not in code_only
    assert "0.756737485808578692" not in code_only  # historical BR_BB


def test_write_point_artifacts_records_provenance_and_ownership() -> None:
    new = load_new()
    manifest = {
        "point_id": "P_test_500",
        "model_variant": "FACTORIZED_G_ONLY",
        "m_h_GeV": "125.13",
        "m_H2_GeV": "500.0",
        "g_hH2H2_GeV": "20.0",
        "total_width_GeV": "4.56118529862185007e-14",
        "ctau_physical_mm": "4.32622152973311191",
        "ctau_response_mm": "50.0",
        "lifetime_mode": "DETECTOR_RESPONSE_EXPERIMENT",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        point = new.validate_point_manifest(manifest)
        out_dir = new.build_point(PACK_A, point, root)
        result = json.loads((out_dir / "point.json").read_text())

        assert result["point_id"] == "P_test_500"
        assert result["model_variant"] == "FACTORIZED_G_ONLY"
        assert result["Mh2_GeV"] == 500.0
        assert result["GHphiphi_GeV"] == 20.0
        assert result["madgraph_decay_ownership"] == "H2 stable in LHE"
        assert "downstream" in result["pythia_decay_ownership"].lower()
        assert result["source_pack_a_sha256"]
        assert result["ufo_sha256"]
        assert (out_dir / "ufo_overlay.zip").exists()
        with zipfile.ZipFile(out_dir / "ufo_overlay.zip") as archive:
            names = archive.namelist()
            assert any(n.endswith("parameters.py") for n in names)
            assert any(n.endswith("couplings.py") for n in names)


def test_rejects_unsupported_model_variant() -> None:
    new = load_new()
    with pytest.raises(ValueError, match="unsupported model_variant"):
        new.validate_point_manifest(
            {
                "point_id": "p",
                "model_variant": "PHYSICAL_DECAYS_NO_HEAVY_CASCADES",
                "m_H2_GeV": "300.0",
                "g_hH2H2_GeV": "10.0",
            }
        )


def test_rejects_missing_required_field() -> None:
    new = load_new()
    with pytest.raises(ValueError, match="missing required field: g_hH2H2_GeV"):
        new.validate_point_manifest(
            {
                "point_id": "p",
                "model_variant": "FACTORIZED_G_ONLY",
                "m_H2_GeV": "300.0",
            }
        )


def test_rejects_unsupported_ghphiphi_convention() -> None:
    new = load_new()
    with pytest.raises(ValueError, match="unsupported ghphiphi_convention"):
        new.validate_point_manifest(
            {
                "point_id": "p",
                "model_variant": "FACTORIZED_G_ONLY",
                "m_H2_GeV": "300.0",
                "g_hH2H2_GeV": "10.0",
                "ghphiphi_convention": "abs_value_with_separate_sign",
            }
        )


def test_format_ufo_scientific_exact_decimal_round_trip() -> None:
    new = load_new()
    # This is the exact case the module docstring calls out: a plain Python
    # float format of 125.13 does NOT reproduce the historical hardcoded
    # text, but Decimal-based formatting of the same string does.
    assert f"{125.13:.17e}" != "1.25130000000000000e+02"
    assert new.format_ufo_scientific("125.13") == "1.25130000000000000e+02"
    assert new.format_ufo_scientific("150.0") == "1.50000000000000000e+02"
    assert new.format_ufo_scientific("0") == "0.00000000000000000e+00"


def test_format_ufo_scientific_rejects_excess_precision() -> None:
    new = load_new()
    with pytest.raises(ValueError, match="significant decimal digits"):
        new.format_ufo_scientific("1.234567890123456789012345")  # far more than 18 sig figs


def test_manifest_round_trip_through_file(tmp_path) -> None:
    new = load_new()
    manifest_path = tmp_path / "point.json"
    manifest_path.write_text(json.dumps(HISTORICAL_MANIFEST))
    point, digest, raw = new.load_point_manifest(manifest_path)
    assert point.point_id == "H2scan_mH150_tb300000"
    assert digest == new.sha256_bytes(raw)
    assert len(digest) == 64
