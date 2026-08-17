#!/usr/bin/env python3
"""Build one deterministic Pack B MODEL_DERIVED UFO overlay from Pack A.

FROZEN BENCHMARK BUILDER -- not a generic generator.

Every physical value below is hard-coded to the validated 150 GeV benchmark
H2scan_mH150_tb300000, including the SM-like scalar mass. That mass is the
HISTORICAL convention mh = 125.13 GeV (MH_CONVENTION), deliberately NOT the
canonical mh = 125.20 GeV now declared in the dihiggs ecosystem's
conventions/physics_conventions.yaml (sm_like_higgs.m_h_GeV).

Do not migrate MEDIATOR_MASS_GEV / MEDIATOR_MASS_TEXT to the canonical value.
Doing so would reinterpret a frozen, released artifact as a newly calculated
point: the released param_card, its point.json and the byte-identical release
hashes all encode 125.13, and pack_b/tests/test_model_derived.py locks them.

For NEW physical points use the generic builder, which takes m_h_GeV from the
canonical point manifest with no default at all. See
docs/PHYSICAL_POINT_UFO_HANDOFF.md, section "SM-like Higgs mass convention".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


POINT_ID = "H2scan_mH150_tb300000"
MASS_GEV = 150.0
# HISTORICAL mass convention of this frozen benchmark. The canonical convention
# for new production is 125.20 (conventions/physics_conventions.yaml). See the
# module docstring before changing anything below.
MH_CONVENTION = "historical_125.13"
MEDIATOR_MASS_GEV = 125.13
MEDIATOR_MASS_TEXT = "1.25130000000000000e+02"
CTAU_MM = 4.32622152973311191
CTAU_M = CTAU_MM / 1000.0
CTAU_M_TEXT = "4.32622152973311191e-03"
GH_PHI_PHI = -63.5914252007596588
WIDTH_GEV = 4.56118529862185007e-14
WIDTH_TOLERANCE_GEV = 1e-21
BR_BB = 0.756737485808578692
BR_BB_SQUARED = BR_BB * BR_BB
BR_BB_PROVENANCE = {
    "repository": "fbientrigo/dihiggs",
    "benchmark_commit": "92ad4d80f537bffd8663e42f1c6881e82849feab",
    "path": "benchmarks/FIRST_H2_RECAST_CANDIDATE.json",
    "sha256": "c8a65f1bb0c75b48b3fd0571d5e3c1ee5dcb3388222ae50d087f102a92c0af98",
    "field": "selected_candidate.br_bb",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"expected one match for {pattern!r}, found {count}")
    return updated


def patch_parameters(text: str) -> str:
    text = replace_once(text, r"(ctauh2 = Parameter\(.*?\n(?:.*\n){2}\s+value = )0\.1,", rf"\g<1>{CTAU_M_TEXT},")
    text = replace_once(text, r"(MH = Parameter\(.*?\n(?:.*\n){2}\s+value = )125,", rf"\g<1>{MEDIATOR_MASS_TEXT},")
    text = replace_once(text, r"(Mh2 = Parameter\(.*?\n(?:.*\n){2}\s+value = )200,", rf"\g<1>{MASS_GEV:.17e},")
    marker = "\nMZ = Parameter(name = 'MZ',"
    addition = (
        "\nGHphiphi = Parameter(name = 'GHphiphi',\n"
        "                       nature = 'external',\n"
        "                       type = 'real',\n"
        f"                       value = {GH_PHI_PHI:.17e},\n"
        "                       texname = '\\\\text{GHphiphi}',\n"
        "                       lhablock = 'FRBlock',\n"
        "                       lhacode = [ 3 ])\n"
    )
    return text.replace(marker, addition + marker, 1)


def patch_couplings(text: str) -> str:
    return replace_once(text, r"value = '8\*complex\(0,1\)\*Mh2\*\*2/vev'", "value = 'complex(0,1)*GHphiphi'")


def patched_members(source: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(source) as archive:
        marker = "/model/LLscalar_v3_UFO_runtime/"
        members = {
            info.filename: archive.read(info.filename)
            for info in archive.infolist()
            if marker in f"/{info.filename}" and not info.filename.endswith("py3_model.pkl")
        }
    parameter = next(name for name in members if name.endswith("model/LLscalar_v3_UFO_runtime/parameters.py"))
    coupling = next(name for name in members if name.endswith("model/LLscalar_v3_UFO_runtime/couplings.py"))
    members[parameter] = patch_parameters(members[parameter].decode()).encode()
    members[coupling] = patch_couplings(members[coupling].decode()).encode()
    return members


def write_deterministic_zip(members: dict[str, bytes], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith("/") else 0o644) << 16
            archive.writestr(info, members[name])


def write_contract(output_dir: Path, source: Path, archive: Path) -> None:
    width = 1.9732698e-16 / CTAU_M
    if abs(width - WIDTH_GEV) > WIDTH_TOLERANCE_GEV:
        raise ValueError("ctau-to-width replay failed")
    point = {
        "schema": "dihiggs.pack_b.model_derived.v1",
        "point_id": POINT_ID,
        "model_pack": "pack_b_h2_model_derived_v1",
        "coupling_mode": "MODEL_DERIVED",
        "Mh2_GeV": MASS_GEV,
        "ctauh2_m": CTAU_M,
        "ctau_mm": CTAU_MM,
        "GHphiphi_GeV": GH_PHI_PHI,
        "width_GeV": width,
        "width_target_GeV": WIDTH_GEV,
        "width_tolerance_GeV": WIDTH_TOLERANCE_GEV,
        "br_bb": BR_BB,
        "br_bb_squared": BR_BB_SQUARED,
        "br_bb_provenance": BR_BB_PROVENANCE,
        "madgraph_rerun_required": False,
        "madgraph_rerun_reason": "existing production card already used MH=125.13 and all other physical inputs are unchanged",
        "pdg_mediator": 25,
        "pdg_h2": 9000006,
        "madgraph_decay_ownership": "H2 stable in LHE",
        "pythia_decay_ownership": "lifetime = 4.32622152973311191 mm; forced H2 -> bb for sample efficiency",
        "physical_event_normalization": "sigma_H2H2 * br_bb^2",
        "source_pack_a_sha256": sha256(source),
        "ufo_sha256": sha256(archive),
        "forbidden_active_values": ["PI_FIXED", "Mbar2_GeV2", "default Mh2 = 200", "default ctauh2 = 0.1"],
    }
    (output_dir / "point.json").write_text(json.dumps(point, indent=2, sort_keys=True) + "\n")
    (output_dir / "param_card.dat").write_text(
        "Block MASS\n"
        f"  25 {MEDIATOR_MASS_TEXT} # SM-like scalar\n"
        "  9000006 1.50000000000000000e+02 # H2\n"
        "Block FRBlock\n"
        f"  2 {CTAU_M_TEXT} # ctauh2 [m]\n"
        f"  3 {GH_PHI_PHI:.17e} # GHphiphi [GeV]\n"
    )
    (output_dir / "RUNTIME_CONTRACT.md").write_text(
        "# H2 model-derived runtime contract\n\n"
        "- MadGraph: H2 stable in LHE.\n"
        "- Pythia: configure PDG 9000006 with tau0 = 4.32622152973311191 mm and force H2 -> bb.\n"
        "- Physical normalization: `sigma_H2H2 * br_bb^2`; forced decay changes sampling only.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack-a", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    members = patched_members(args.pack_a)
    write_deterministic_zip(members, args.output)
    write_contract(args.output.parent, args.pack_a, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
