import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generator_closure as gc


def test_metric_and_histogram_are_finite_and_record_counts():
    metric = gc.metric("x", [0.0, 1.0, 2.0], [0.0, 1.0, 3.0], "GeV", "MG", "Pythia")
    rows = list(gc.hist_rows("x", [0.0, 1.0, 2.0], [0.0, 1.0, 3.0], "MG", "Pythia", bins=3))
    assert metric["n_left"] == metric["n_right"] == 3
    assert len(rows) == 3
    assert sum(r["left_n"] for r in rows) == 9
    assert all("ratio_stat_unc" in row for row in rows)


def test_parent_decay_residual_closes_exactly_for_known_four_vectors():
    class D:
        px, py, pz, e = 1.0, 0.0, 0.0, 1.0

    class H:
        px, py, pz, e = 2.0, 0.0, 0.0, 2.0
        direct_daughters = [D(), D()]

    class T:
        h2 = [H()]

    row = {"event": 1, "truth": T()}
    residual = gc.residual_rows([row], "D0")[0]
    assert max(abs(residual[key]) for key in ("delta_px_GeV", "delta_py_GeV", "delta_pz_GeV", "delta_E_GeV")) == 0.0
