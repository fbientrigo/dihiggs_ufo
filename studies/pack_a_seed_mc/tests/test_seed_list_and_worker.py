import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pack_a_seed_mc import config, pack_a_worker


def test_seed_list_has_30_unique_seeds():
    seeds = config.load_seed_list()
    assert len(seeds) == 30
    assert len(set(seeds)) == 30


def test_seed_list_includes_canonical_seeds_first():
    seeds = config.load_seed_list()
    assert seeds[0] == 12345
    assert seeds[1] == 67890


def test_sha256_of_matches_known_content(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello world")
    assert pack_a_worker.sha256_of(p) == hashlib.sha256(b"hello world").hexdigest()


def test_verify_frozen_zip_rejects_hash_mismatch(tmp_path, monkeypatch):
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"not the real pack a bytes")
    monkeypatch.setenv("PACK_A_FROZEN_ZIP", str(bad_zip))
    with pytest.raises(pack_a_worker.PackAError):
        pack_a_worker.verify_frozen_zip()


def test_patch_seed_whitelist_is_idempotent(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text(
        'declare -A PACK_A_SEED_CONFIGS=(\n'
        '  [12345]="points/A_PI_NATIVE_200.yaml"\n'
        '  [67890]="points/A_PI_NATIVE_200_seed67890.yaml"\n'
        ')\n'
    )
    pack_a_worker._patch_seed_whitelist(script, 99999, "points/A_PI_NATIVE_200_seed99999.yaml")
    once = script.read_text()
    assert once.count("[99999]=") == 1

    pack_a_worker._patch_seed_whitelist(script, 99999, "points/A_PI_NATIVE_200_seed99999.yaml")
    twice = script.read_text()
    assert twice.count("[99999]=") == 1
    assert once == twice


def test_patch_seed_whitelist_missing_anchor_raises(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text("declare -A SOMETHING_ELSE=()\n")
    with pytest.raises(pack_a_worker.PackAError):
        pack_a_worker._patch_seed_whitelist(script, 1, "points/x.yaml")


def _build_fixture_pack_root(tmp_path):
    pack_root = tmp_path / "pi_ufo_baseline_v1_release_candidate_hotfix1"
    (pack_root / "points").mkdir(parents=True)
    (pack_root / "bin" / "lib").mkdir(parents=True)
    (pack_root / "points" / "A_PI_NATIVE_200.yaml").write_text(
        "model_pack: pi_ufo_baseline_v1\n"
        "point_id: A_PI_NATIVE_200\n\n"
        "mphi_GeV: 200.0\n"
        "coupling_mode: PI_FIXED\n\n"
        "ctau_mm: 100.0\n\n"
        "branching_ratios:\n"
        "  bb: 0.00\n"
        "  gammagamma: 1.00\n\n"
        "seed: 12345\n"
    )
    (pack_root / "bin" / "lib" / "run.sh").write_text(
        'declare -A PACK_A_SEED_CONFIGS=(\n'
        '  [12345]="points/A_PI_NATIVE_200.yaml"\n'
        '  [67890]="points/A_PI_NATIVE_200_seed67890.yaml"\n'
        ')\n'
    )
    return pack_root


def test_ensure_seed_config_only_changes_seed_and_point_id(tmp_path):
    pack_root = _build_fixture_pack_root(tmp_path)
    worker = pack_a_worker.Worker(seed=54321, worker_dir=tmp_path, pack_root=pack_root)

    rel_config = pack_a_worker.ensure_seed_config(worker)

    template_lines = (pack_root / "points" / "A_PI_NATIVE_200.yaml").read_text().splitlines()
    generated_lines = (pack_root / rel_config).read_text().splitlines()
    assert len(template_lines) == len(generated_lines)

    changed = [
        (t, g) for t, g in zip(template_lines, generated_lines) if t != g
    ]
    assert len(changed) == 2
    changed_prefixes = {line.split(":")[0].strip() for _, line in changed}
    assert changed_prefixes == {"point_id", "seed"}
    assert f"seed: {worker.seed}" in generated_lines

    run_sh_text = (pack_root / "bin" / "lib" / "run.sh").read_text()
    assert f"[{worker.seed}]=" in run_sh_text


def test_ensure_seed_config_canonical_seed_does_not_touch_filesystem(tmp_path):
    pack_root = _build_fixture_pack_root(tmp_path)
    before = (pack_root / "bin" / "lib" / "run.sh").read_text()
    worker = pack_a_worker.Worker(seed=12345, worker_dir=tmp_path, pack_root=pack_root)

    rel_config = pack_a_worker.ensure_seed_config(worker)

    assert rel_config == "points/A_PI_NATIVE_200.yaml"
    after = (pack_root / "bin" / "lib" / "run.sh").read_text()
    assert before == after


def test_ensure_seed_config_raises_if_seed_substitution_fails(tmp_path, monkeypatch):
    pack_root = _build_fixture_pack_root(tmp_path)
    worker = pack_a_worker.Worker(seed=54321, worker_dir=tmp_path, pack_root=pack_root)

    # Simulate a template that no longer contains the expected anchor line,
    # so the substitution silently fails to insert the new seed.
    template_path = pack_root / "points" / "A_PI_NATIVE_200.yaml"
    template_path.write_text(template_path.read_text().replace("seed: 12345", "seed_value: 12345"))

    with pytest.raises(pack_a_worker.PackAError):
        pack_a_worker.ensure_seed_config(worker)
