"""Builds the artifact checksum manifest and result bundle ZIP."""
from __future__ import annotations

import zipfile
from pathlib import Path

from .pack_a_worker import sha256_of


def write_checksums(root: Path, output: Path, exclude_names: set[str] | None = None) -> None:
    exclude_names = exclude_names or set()
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in exclude_names:
            rel = path.relative_to(root)
            lines.append(f"{sha256_of(path)}  {rel}")
    output.write_text("\n".join(lines) + ("\n" if lines else ""))


def build_zip(root: Path, output_zip: Path, exclude_names: set[str] | None = None) -> None:
    exclude_names = exclude_names or set()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name not in exclude_names and path != output_zip:
                zf.write(path, path.relative_to(root))


def verify_checksums(root: Path, checksums_file: Path) -> list[str]:
    """Returns a list of mismatch descriptions; empty if all match."""
    mismatches = []
    for line in checksums_file.read_text().splitlines():
        if not line.strip():
            continue
        expected_hash, rel = line.split("  ", 1)
        path = root / rel
        if not path.is_file():
            mismatches.append(f"missing: {rel}")
            continue
        actual = sha256_of(path)
        if actual != expected_hash:
            mismatches.append(f"mismatch: {rel}")
    return mismatches
