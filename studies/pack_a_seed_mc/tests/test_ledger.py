import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pack_a_seed_mc import ledger


def test_ensure_seeds_marks_pending(tmp_path):
    data = {"seeds": {}}
    ledger.ensure_seeds(data, [1, 2, 3])
    assert all(ledger.status_of(data, s) == "pending" for s in (1, 2, 3))


def test_ensure_seeds_does_not_reset_completed():
    data = {"seeds": {}}
    ledger.ensure_seeds(data, [1])
    ledger.mark_completed(data, 1, {"seed": 1, "sigma_pb": 0.02})
    ledger.ensure_seeds(data, [1, 2])
    assert ledger.status_of(data, 1) == "completed"
    assert ledger.status_of(data, 2) == "pending"


def test_mark_failed_records_stay_in_ledger():
    data = {"seeds": {}}
    ledger.ensure_seeds(data, [5])
    ledger.mark_failed(data, 5, {"seed": 5, "exit_status": 1, "classification": "FAILED"})
    assert ledger.status_of(data, 5) == "failed"
    failed = ledger.failed_records(data)
    assert len(failed) == 1
    assert failed[0]["seed"] == 5
    # a failed seed is never silently dropped from completed_records either way
    assert ledger.completed_records(data) == []


def test_completed_records_sorted_by_seed():
    data = {"seeds": {}}
    ledger.ensure_seeds(data, [3, 1, 2])
    for s in (3, 1, 2):
        ledger.mark_completed(data, s, {"seed": s, "sigma_pb": 0.02})
    records = ledger.completed_records(data)
    assert [r["seed"] for r in records] == [1, 2, 3]


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "ledger.json"
    data = {"seeds": {}}
    ledger.ensure_seeds(data, [1, 2])
    ledger.mark_completed(data, 1, {"seed": 1, "sigma_pb": 0.02})
    ledger.save(path, data)
    loaded = ledger.load(path)
    assert ledger.status_of(loaded, 1) == "completed"
    assert ledger.status_of(loaded, 2) == "pending"
