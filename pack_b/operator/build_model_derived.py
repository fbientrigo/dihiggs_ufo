#!/usr/bin/env python3
"""Generic, point-driven Pack B MODEL_DERIVED UFO overlay builder.

This module generalizes `build_model_derived.py` (which hardcodes exactly one
historical benchmark point, `H2scan_mH150_tb300000`, as module-level
constants) into a point-manifest-driven builder for the `FACTORIZED_G_ONLY`
production variant.

Physics scope (verified against the actual UFO source, see
`releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip` ->
`model/LLscalar_v3_UFO_runtime/` and its `MODEL_CARD.md`):

- The model is a toy "LLscalar" extension of the SM: one extra real neutral
  scalar `h2` (PDG 9000006), no pseudoscalar `A`, no charged Higgs, no
  `tan_beta`/`lambda1..7`. This is documented in the Pack A
  `KNOWN_LIMITATIONS.md` and confirmed here by direct inspection.
- Production is `gg -> H*(125 GeV, finite-mass ggH form factor) -> h2 h2`,
  i.e. genuine `pp -> H2 H2` pair production via an s-channel SM-Higgs-like
  mediator. The mediator-to-h2h2 vertex `V_7 = (H, h2, h2)` uses coupling
  `GC_90`, whose value UFO text is patched from the historical constant
  `'8*complex(0,1)*Mh2**2/vev'` to `'complex(0,1)*GHphiphi'` by
  `patch_couplings()` below (same regex logic as the historical builder).
  This means `Mh2` and `GHphiphi` genuinely and completely parameterize this
  production amplitude at the level this UFO model supports -- there is no
  blocked capability here for `FACTORIZED_G_ONLY`. (A full 2HDM UFO with
  independent `mA`/`mHp`/`tan_beta` is a *separate*, larger gap -- see
  `docs/UFO_GENERICIZATION_REQUIREMENTS.md` Gap 1 -- but it is not required
  for this variant.)
- `h2`'s own width (`Wh2 = 1.9732698e-16/ctauh2`, in GeV, with `ctauh2` in
  metres) does NOT enter this production amplitude: `h2` is a final-state
  particle in the `gg -> H* -> h2 h2` topology, not an internal propagator,
  so its width is irrelevant to the LHE-level 2-to-2 production cross
  section as long as it is emitted stable (no MadGraph-level decay
  requested). `ctauh2` is nonetheless still patched into the UFO parameter
  card, purely as a bookkeeping/continuity field: the historical builder
  patches it so that the same param card can carry the physical lifetime
  value through to the downstream Pythia stage. Per the mission's ownership
  split ("H2 decay and response lifetime are owned downstream"), this
  builder requires the canonical physical and response lifetime fields so a
  caller cannot silently conflate them. The production amplitude itself is
  independent of the H2 width because H2 is stable in the LHE.

Manifest schema (documented in full in
`docs/MODEL_DERIVED_MANIFEST.md`): required fields `point_id`, `model_variant`
(`"FACTORIZED_G_ONLY"`), `m_h_GeV`, `m_H2_GeV`, `g_hH2H2_GeV`,
`total_width_GeV`, `ctau_physical_mm`, `ctau_response_mm`, and `lifetime_mode`.
`BR_bb` and provenance are optional bookkeeping fields.

Numeric fields are decimal strings, not JSON floats/Python floats. This is
deliberate, not stylistic: several of the historical benchmark's own
constants (`MEDIATOR_MASS_GEV = 125.13`, `CTAU_MM = 4.32622152973311191`)
cannot be round-tripped exactly through IEEE-754 float64 and back to the
UFO's `%.17e`-style text form -- e.g. `f"{125.13:.17e}"` yields
`"1.25129999999999995e+02"`, not the historical
`"1.25130000000000000e+02"`. `format_ufo_scientific()` below parses inputs
with `decimal.Decimal` instead, so any exact finite-decimal input (as
supplied by an upstream point database or copied verbatim from a historical
constant's own source text) reproduces the intended digit string exactly.
This is what makes the mandatory historical-anchor regression test
byte-identical without any point-specific special-casing.

Coupling convention for `g_hH2H2_GeV` -- READ BEFORE REUSING:

This builder's `"direct"` convention (the only one implemented) sets
`GHphiphi := g_hH2H2_GeV` verbatim, with no sign flip. This matches the
historical benchmark exactly: `build_model_derived.py`'s
`GH_PHI_PHI = -63.5914252007596588` is already negative, and the mission's
own historical regression anchor quotes the identical signed value under the
name `g_hH2H2_GeV`. However, `docs/PHYSICAL_POINT_UFO_HANDOFF.md` documents
a *different* convention for a same-named quantity:

    2HDMC: c = -i g
    g_hH2H2_GeV = abs(Im(c))      # always >= 0
    UFO: GHphiphi = Im(c) = -g_hH2H2_GeV

i.e. that document's `g_hH2H2_GeV` is a non-negative magnitude, with the
sign applied separately. This module does NOT implement that convention
(there is no evidence in this repo of which of the two a general upstream
caller intends), and `validate_point_manifest()` will reject any
`ghphiphi_convention` other than `"direct"` rather than silently guessing.
A future caller that only has the magnitude-only quantity from
`PHYSICAL_POINT_UFO_HANDOFF.md`'s convention must apply
`GHphiphi = -g_hH2H2_GeV` itself before calling this builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional


SCHEMA = "dihiggs.pack_b.model_derived.generic.v1"
SUPPORTED_MODEL_VARIANT = "FACTORIZED_G_ONLY"
SUPPORTED_GHPHIPHI_CONVENTIONS = ("direct",)
PHYSICAL_LIFETIME_MODE = "PHYSICAL_PREDICTION"
RESPONSE_LIFETIME_MODE = "DETECTOR_RESPONSE_EXPERIMENT"

RUNTIME_MARKER = "/model/LLscalar_v3_UFO_runtime/"

# hbar*c, GeV*m. Physical constant (not a benchmark parameter), reused from
# the historical builder's width<->ctau replay check.
HBAR_C_GEV_M = Decimal("1.9732698e-16")
HBAR_C_GEV_MM = Decimal("1.973269804e-13")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"expected one match for {pattern!r}, found {count}")
    return updated


def format_ufo_scientific(value: Any) -> str:
    """Format a decimal-exact value as UFO-style 18-significant-digit scientific notation.

    Parses `value` with `decimal.Decimal` (never through `float`) so exact
    finite-decimal inputs are reproduced digit-for-digit. Raises `ValueError`
    if `value` carries more than 18 significant decimal digits, rather than
    silently rounding -- callers that intend to lose precision should round
    explicitly before calling this.
    """
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"cannot parse {value!r} as a decimal number") from exc
    if d == 0:
        return "0.00000000000000000e+00"
    sign, digits, exp = d.as_tuple()
    ndigits = len(digits)
    first_exp = exp + ndigits - 1
    want = 18
    if ndigits < want:
        digits = list(digits) + [0] * (want - ndigits)
    elif ndigits > want:
        raise ValueError(
            f"{value!r} has {ndigits} significant decimal digits; "
            f"format_ufo_scientific only supports <= {want} without rounding. "
            "Round the input explicitly upstream if precision loss is intended."
        )
    mantissa = "".join(str(x) for x in digits)
    mantissa_text = f"{mantissa[0]}.{mantissa[1:want]}"
    sign_text = "-" if sign else ""
    exp_sign = "+" if first_exp >= 0 else "-"
    return f"{sign_text}{mantissa_text}e{exp_sign}{abs(first_exp):02d}"


@dataclass(frozen=True)
class PointManifest:
    point_id: str
    model_variant: str
    m_h_GeV: str
    m_H2_GeV: str
    g_hH2H2_GeV: str
    total_width_GeV: str
    ctau_physical_mm: str
    ctau_response_mm: str
    lifetime_mode: str
    ghphiphi_convention: str = "direct"
    BR_bb: Optional[str] = None
    BR_bb_provenance: Optional[dict] = None
    extra_provenance: dict = field(default_factory=dict)

    @property
    def ctau_m(self) -> Decimal:
        return Decimal(str(self.ctau_physical_mm)) / Decimal(1000)

    @property
    def response_ctau_m(self) -> Decimal:
        return Decimal(str(self.ctau_response_mm)) / Decimal(1000)


def validate_point_manifest(raw: dict) -> PointManifest:
    """Validate a raw manifest dict and return a `PointManifest`.

    Raises `ValueError` (with all problems collected, not just the first)
    if the manifest is invalid.
    """
    errors: list[str] = []

    def require(key: str):
        value = raw.get(key)
        if value in (None, ""):
            errors.append(f"missing required field: {key}")
            return None
        return value

    point_id = require("point_id")
    variant = require("model_variant")
    mh = require("m_h_GeV")
    mh2 = require("m_H2_GeV")
    ghh = require("g_hH2H2_GeV")
    total_width = require("total_width_GeV")
    ctau_physical = require("ctau_physical_mm")
    ctau_response = require("ctau_response_mm")
    lifetime_mode = require("lifetime_mode")

    if variant is not None and variant != SUPPORTED_MODEL_VARIANT:
        errors.append(
            f"unsupported model_variant {variant!r}; only "
            f"{SUPPORTED_MODEL_VARIANT!r} is implemented by this builder"
        )

    if lifetime_mode not in {PHYSICAL_LIFETIME_MODE, RESPONSE_LIFETIME_MODE}:
        errors.append(
            f"unsupported lifetime_mode {lifetime_mode!r}; only "
            f"{PHYSICAL_LIFETIME_MODE!r} and {RESPONSE_LIFETIME_MODE!r} are accepted"
        )
    if lifetime_mode == RESPONSE_LIFETIME_MODE and variant != SUPPORTED_MODEL_VARIANT:
        errors.append(f"{RESPONSE_LIFETIME_MODE} is only valid for {SUPPORTED_MODEL_VARIANT}")

    convention = raw.get("ghphiphi_convention", "direct")
    if convention not in SUPPORTED_GHPHIPHI_CONVENTIONS:
        errors.append(
            f"unsupported ghphiphi_convention {convention!r}; only "
            f"{SUPPORTED_GHPHIPHI_CONVENTIONS} implemented (see module docstring "
            "re: docs/PHYSICAL_POINT_UFO_HANDOFF.md's abs-value convention)"
        )

    for label, value in (
        ("m_h_GeV", mh),
        ("m_H2_GeV", mh2),
        ("g_hH2H2_GeV", ghh),
        ("total_width_GeV", total_width),
        ("ctau_physical_mm", ctau_physical),
        ("ctau_response_mm", ctau_response),
    ):
        if value is None:
            continue
        try:
            format_ufo_scientific(value)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")

    BR_bb = raw.get("BR_bb")
    if BR_bb is not None:
        try:
            float(BR_bb)
        except (TypeError, ValueError):
            errors.append(f"BR_bb: cannot parse {BR_bb!r} as a number")

    if errors:
        raise ValueError("invalid point manifest:\n  " + "\n  ".join(errors))

    width = Decimal(str(total_width))
    physical = Decimal(str(ctau_physical))
    response = Decimal(str(ctau_response))
    expected_physical_mm = HBAR_C_GEV_MM / width
    if width <= 0 or physical <= 0 or response <= 0:
        raise ValueError("total_width_GeV and both lifetime fields must be positive")
    if abs(physical - expected_physical_mm) / expected_physical_mm > Decimal("1e-9"):
        raise ValueError(
            "ctau_physical_mm must equal hbar_c / total_width_GeV"
        )
    if lifetime_mode == PHYSICAL_LIFETIME_MODE and abs(response - physical) / physical > Decimal("1e-9"):
        raise ValueError("physical lifetime mode requires ctau_response_mm == ctau_physical_mm")

    return PointManifest(
        point_id=str(point_id),
        model_variant=str(variant),
        m_h_GeV=str(mh),
        m_H2_GeV=str(mh2),
        g_hH2H2_GeV=str(ghh),
        total_width_GeV=str(total_width),
        ctau_physical_mm=str(ctau_physical),
        ctau_response_mm=str(ctau_response),
        lifetime_mode=str(lifetime_mode),
        ghphiphi_convention=str(convention),
        BR_bb=(str(BR_bb) if BR_bb is not None else None),
        BR_bb_provenance=raw.get("BR_bb_provenance"),
        extra_provenance=raw.get("provenance", {}),
    )


def load_point_manifest(path: Path) -> tuple[PointManifest, str, bytes]:
    """Load and validate a point manifest file.

    Returns `(point, manifest_sha256, manifest_bytes)` so callers can record
    input provenance without re-reading the file.
    """
    raw_bytes = Path(path).read_bytes()
    raw = json.loads(raw_bytes.decode())
    point = validate_point_manifest(raw)
    return point, sha256_bytes(raw_bytes), raw_bytes


def patch_parameters(
    text: str,
    *,
    mh2_text: str,
    mediator_mass_text: str,
    ctau_m_text: str,
    ghphiphi_text: str,
) -> str:
    """Patch `parameters.py`. Same regex logic as `build_model_derived.patch_parameters`,
    generalized to take pre-formatted value text instead of module constants."""
    text = replace_once(
        text,
        r"(ctauh2 = Parameter\(.*?\n(?:.*\n){2}\s+value = )0\.1,",
        rf"\g<1>{ctau_m_text},",
    )
    text = replace_once(
        text,
        r"(MH = Parameter\(.*?\n(?:.*\n){2}\s+value = )125,",
        rf"\g<1>{mediator_mass_text},",
    )
    text = replace_once(
        text,
        r"(Mh2 = Parameter\(.*?\n(?:.*\n){2}\s+value = )200,",
        rf"\g<1>{mh2_text},",
    )
    marker = "\nMZ = Parameter(name = 'MZ',"
    addition = (
        "\nGHphiphi = Parameter(name = 'GHphiphi',\n"
        "                       nature = 'external',\n"
        "                       type = 'real',\n"
        f"                       value = {ghphiphi_text},\n"
        "                       texname = '\\\\text{GHphiphi}',\n"
        "                       lhablock = 'FRBlock',\n"
        "                       lhacode = [ 3 ])\n"
    )
    return text.replace(marker, addition + marker, 1)


def patch_couplings(text: str) -> str:
    """Patch `couplings.py`. Identical to `build_model_derived.patch_couplings`
    -- this is a structural rewrite of vertex V_7's coupling formula, the same
    for every point, not a per-point value."""
    return replace_once(
        text,
        r"value = '8\*complex\(0,1\)\*Mh2\*\*2/vev'",
        "value = 'complex(0,1)*GHphiphi'",
    )


def patched_members(source: Path, point: PointManifest) -> dict[str, bytes]:
    with zipfile.ZipFile(source) as archive:
        members = {
            info.filename: archive.read(info.filename)
            for info in archive.infolist()
            if RUNTIME_MARKER in f"/{info.filename}" and not info.filename.endswith("py3_model.pkl")
        }
    parameter_name = next(name for name in members if name.endswith("model/LLscalar_v3_UFO_runtime/parameters.py"))
    coupling_name = next(name for name in members if name.endswith("model/LLscalar_v3_UFO_runtime/couplings.py"))

    ghphiphi_text = format_ufo_scientific(point.g_hH2H2_GeV)  # "direct" convention: GHphiphi := g_hH2H2_GeV
    members[parameter_name] = patch_parameters(
        members[parameter_name].decode(),
        mh2_text=format_ufo_scientific(point.m_H2_GeV),
        mediator_mass_text=format_ufo_scientific(point.m_h_GeV),
        ctau_m_text=format_ufo_scientific(point.ctau_m),
        ghphiphi_text=ghphiphi_text,
    ).encode()
    members[coupling_name] = patch_couplings(members[coupling_name].decode()).encode()
    return members


def write_deterministic_zip(members: dict[str, bytes], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith("/") else 0o644) << 16
            archive.writestr(info, members[name])


def write_point_artifacts(
    output_dir: Path,
    source: Path,
    archive: Path,
    point: PointManifest,
    *,
    manifest_path: Optional[Path] = None,
    manifest_sha256: Optional[str] = None,
) -> dict:
    """Write `point.json`, `param_card.dat`, and `RUNTIME_CONTRACT.md` for one point."""
    output_dir.mkdir(parents=True, exist_ok=True)

    mediator_text = format_ufo_scientific(point.m_h_GeV)
    mh2_text = format_ufo_scientific(point.m_H2_GeV)
    ctau_m_text = format_ufo_scientific(point.ctau_m)
    ghphiphi_text = format_ufo_scientific(point.g_hH2H2_GeV)

    ctau_m_decimal = point.ctau_m
    width_gev = float(Decimal(point.total_width_GeV))

    BR_bb = float(point.BR_bb) if point.BR_bb is not None else None

    result = {
        "schema": SCHEMA,
        "point_id": point.point_id,
        "model_pack": "pack_b_h2_model_derived_generic_v1",
        "coupling_mode": "MODEL_DERIVED",
        "model_variant": point.model_variant,
        "production_process": (
            "pp -> H2 H2 via gg -> H*(finite-mass ggH form factor) -> H2 H2; "
            "H-h2-h2 vertex GC_90 patched to 'complex(0,1)*GHphiphi'. "
            "See MODEL_CARD.md in the Pack A source and this module's docstring."
        ),
        "Mh2_GeV": float(Decimal(point.m_H2_GeV)),
        "m_h_GeV": float(Decimal(point.m_h_GeV)),
        "total_width_GeV": width_gev,
        "ctauh2_m": float(ctau_m_decimal),
        "ctau_physical_mm": float(Decimal(point.ctau_physical_mm)),
        "ctau_response_mm": float(Decimal(point.ctau_response_mm)),
        "lifetime_mode": point.lifetime_mode,
        "GHphiphi_GeV": float(Decimal(point.g_hH2H2_GeV)),
        "ghphiphi_convention": point.ghphiphi_convention,
        "ghphiphi_convention_note": (
            "'direct' convention: GHphiphi := g_hH2H2_GeV verbatim (no sign flip). "
            "See module docstring for the discrepancy with "
            "docs/PHYSICAL_POINT_UFO_HANDOFF.md's abs(Im(c)) magnitude convention."
        ),
        "width_GeV_from_ctauh2": width_gev,
        "width_note": (
            "Informational only. h2 is a final-state particle in the "
            "gg -> H* -> h2 h2 production topology, not an internal propagator, "
            "so this width does not enter the production amplitude."
        ),
        "BR_bb": BR_bb,
        "BR_bb_provenance": point.BR_bb_provenance,
        "provenance": point.extra_provenance,
        "pdg_mediator": 25,
        "pdg_h2": 9000006,
        "madgraph_decay_ownership": "H2 stable in LHE",
        "pythia_decay_ownership": (
            "H2 decay and response lifetime are owned downstream (Pack AA / Pythia "
            "stage). ctauh2 patched into this UFO parameter card is a bookkeeping/"
            "continuity field and is NOT consumed by the pp -> H2 H2 production "
            "amplitude in this topology."
        ),
        "physical_event_normalization": "sigma_H2H2 (downstream forced-decay BR handled separately, if any)",
        "source_pack_a_sha256": sha256(source),
        "ufo_sha256": sha256(archive),
        "input_manifest_path": str(manifest_path) if manifest_path else None,
        "input_manifest_sha256": manifest_sha256,
        "forbidden_active_values": [
            "PI_FIXED",
            "Mbar2_GeV2",
            "default Mh2 = 200",
            "default ctauh2 = 0.1",
            "default MH = 125 is forbidden; the canonical m_h_GeV field is always used",
        ],
        "parameter_provenance": {
            "Mh2_GeV": "manifest.m_H2_GeV",
            "GHphiphi_GeV": "manifest.g_hH2H2_GeV (ghphiphi_convention=direct: no sign flip applied)",
            "m_h_GeV": "manifest.m_h_GeV",
            "ctauh2_m": "manifest.ctau_physical_mm / 1000",
        },
    }
    (output_dir / "point.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output_dir / "param_card.dat").write_text(
        "Block MASS\n"
        f"  25 {mediator_text} # SM-like scalar\n"
        f"  9000006 {mh2_text} # H2\n"
        "Block FRBlock\n"
        f"  2 {ctau_m_text} # ctauh2 [m]\n"
        f"  3 {ghphiphi_text} # GHphiphi [GeV]\n"
    )
    (output_dir / "RUNTIME_CONTRACT.md").write_text(
        f"# H2 model-derived runtime contract -- {point.point_id}\n\n"
        f"- Production variant: `{point.model_variant}`.\n"
        "- MadGraph: H2 stable in LHE; production is `gg -> H* -> H2 H2`.\n"
        f"- Pythia (downstream): configure PDG 9000006 with response lifetime\n"
        f"  `ctau_response_mm` = {point.ctau_response_mm} mm; physical prediction\n"
        f"  `ctau_physical_mm` = {point.ctau_physical_mm} mm.\n"
        "- Physical normalization: `sigma_H2H2`, with any forced-decay branching\n"
        "  ratio applied downstream as a separate sampling-efficiency factor.\n"
    )
    return result


def build_point(pack_a: Path, point: PointManifest, output_root: Path, *, manifest_path: Optional[Path] = None, manifest_sha256: Optional[str] = None) -> Path:
    """End-to-end: patch the UFO overlay for `point` and write it under
    `output_root/<point_id>/`. Returns that directory."""
    output_dir = Path(output_root) / point.point_id
    ufo_zip = output_dir / "ufo_overlay.zip"
    members = patched_members(pack_a, point)
    write_deterministic_zip(members, ufo_zip)
    write_point_artifacts(output_dir, pack_a, ufo_zip, point, manifest_path=manifest_path, manifest_sha256=manifest_sha256)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-a", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="point manifest JSON file")
    parser.add_argument("--output-root", type=Path, required=True, help="artifacts are written under output-root/<point_id>/")
    args = parser.parse_args()
    point, manifest_sha, _ = load_point_manifest(args.manifest)
    build_point(args.pack_a, point, args.output_root, manifest_path=args.manifest, manifest_sha256=manifest_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
