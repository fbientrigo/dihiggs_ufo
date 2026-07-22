import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pack_a_seed_mc import bundle
from pack_a_seed_mc.stats import SeedPoint, summarize
from pack_a_seed_mc import plots

# Fixture-only points; not real MG5 output. Used to prove analysis/rendering
# is reproducible from a results table without rerunning MadGraph.
FIXTURE_POINTS = [
    SeedPoint(12345, 0.02349, 0.0001364),
    SeedPoint(67890, 0.02356, 0.0001374),
    SeedPoint(11111, 0.02351, 0.0001400),
    SeedPoint(22222, 0.02360, 0.0001350),
    SeedPoint(33333, 0.02345, 0.0001300),
]


def test_checksums_roundtrip(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("world")
    checksums = tmp_path / "CHECKSUMS.sha256"
    bundle.write_checksums(tmp_path, checksums, exclude_names={"CHECKSUMS.sha256"})
    mismatches = bundle.verify_checksums(tmp_path, checksums)
    assert mismatches == []


def test_checksums_detect_tampering(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    checksums = tmp_path / "CHECKSUMS.sha256"
    bundle.write_checksums(tmp_path, checksums, exclude_names={"CHECKSUMS.sha256"})
    (tmp_path / "a.txt").write_text("tampered")
    mismatches = bundle.verify_checksums(tmp_path, checksums)
    assert any("mismatch: a.txt" in m for m in mismatches)


def test_build_zip_contains_all_files(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    out_zip = tmp_path.parent / "bundle.zip"
    bundle.build_zip(tmp_path, out_zip)
    import zipfile
    with zipfile.ZipFile(out_zip) as zf:
        assert "a.txt" in zf.namelist()


def test_analysis_and_plots_reproducible_from_fixture_csv_without_rerunning_mg5(tmp_path):
    """Analysis/plot generation must work from a results table alone."""
    summary = summarize(FIXTURE_POINTS, canonical_seeds=(12345, 67890))
    assert summary.n == len(FIXTURE_POINTS)

    out_dir = tmp_path / "figures"
    plots.render_all(FIXTURE_POINTS, summary, out_dir)

    expected_stems = [
        "01_seed_ensemble_forest_plot",
        "02_seed_scatter",
        "03_pull_distribution",
        "04_cumulative_mean",
        "05_reported_error_vs_deviation",
        "06_canonical_seeds_in_ensemble",
    ]
    for stem in expected_stems:
        assert (out_dir / f"{stem}.png").is_file()
        assert (out_dir / f"{stem}.pdf").is_file()
