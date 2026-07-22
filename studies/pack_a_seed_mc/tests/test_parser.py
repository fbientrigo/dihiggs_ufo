import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pack_a_seed_mc import parser

FIXTURE_LHE = """\
<LesHouchesEvents version="3.0">
<event>
9000006 1 0 0 0 0 10.0 5.0 0.0 20.0 0.0
9000006 1 0 0 0 0 -10.0 -5.0 0.0 20.0 0.0
</event>
<event>
9000006 1 0 0 0 0 3.0 4.0 0.0 15.0 0.0
9000006 1 0 0 0 0 -3.0 -4.0 0.0 15.0 0.0
</event>
</LesHouchesEvents>
"""


def _build_fixture_run_dir(tmp_path):
    run_dir = tmp_path / "runs" / "20260101T000000Z_seed99999"
    (run_dir / "events").mkdir(parents=True)
    (run_dir / "events" / "events.lhe").write_text(FIXTURE_LHE)

    manifest = {
        "cross_section": {"sigma_pb": 0.0235, "integration_error_pb": 0.00014, "status": "PASS"},
        "lhe_report": {
            "events": 2,
            "events_with_exactly_two_final_llp": 2,
            "events_with_wrong_final_llp_count": 0,
            "nonfinal_llp_records": 0,
            "llp_stable_in_lhe": True,
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    environment = {
        "python": {"version": "3.12.7"},
        "mg5_bin": "/fake/mg5_aMC",
        "toolchain_expected": "MadGraph5_aMC@NLO 3.5.3",
    }
    (run_dir / "environment.json").write_text(json.dumps(environment))
    (run_dir / "exit_status.txt").write_text("0")
    return run_dir


def test_parse_run_ok_classification(tmp_path):
    run_dir = _build_fixture_run_dir(tmp_path)
    record = parser.parse_run(run_dir, seed=99999, frozen_zip_hash="deadbeef", runtime_seconds=12.3, exit_status=0)
    assert record["seed"] == 99999
    assert record["sigma_pb"] == 0.0235
    assert record["reported_integration_error_pb"] == 0.00014
    assert record["classification"] == "OK"
    assert record["events"] == 2
    assert record["four_momentum_residual_gev"] == 0.0  # both fixture events perfectly balanced


def test_parse_run_failed_when_exit_nonzero(tmp_path):
    run_dir = _build_fixture_run_dir(tmp_path)
    record = parser.parse_run(run_dir, seed=99999, frozen_zip_hash="deadbeef", runtime_seconds=1.0, exit_status=3)
    assert record["classification"] == "FAILED"


def test_parse_run_failed_when_wrong_llp_count(tmp_path):
    run_dir = _build_fixture_run_dir(tmp_path)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    manifest["lhe_report"]["events_with_wrong_final_llp_count"] = 1
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    record = parser.parse_run(run_dir, seed=99999, frozen_zip_hash="deadbeef", runtime_seconds=1.0, exit_status=0)
    assert record["classification"] == "FAILED"


def test_four_momentum_residual_detects_imbalance(tmp_path):
    unbalanced_lhe = """\
<event>
9000006 1 0 0 0 0 10.0 5.0 0.0 20.0 0.0
9000006 1 0 0 0 0 -8.0 -5.0 0.0 20.0 0.0
</event>
"""
    path = tmp_path / "events.lhe"
    path.write_text(unbalanced_lhe)
    residual = parser.four_momentum_residual_gev(path)
    assert residual is not None
    assert residual > 1.9  # sum_px = 2.0, sum_py = 0.0 -> hypot = 2.0


def test_four_momentum_residual_none_for_missing_file(tmp_path):
    assert parser.four_momentum_residual_gev(tmp_path / "missing.lhe") is None
