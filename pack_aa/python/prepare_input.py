#!/usr/bin/env python3
"""Materialize a deterministic 1000-event derivative of Pack A's 100-event LHE."""

from __future__ import annotations

import gzip
import hashlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz"
TARGET = ROOT / "pack_aa/inputs/pack_a_A_PI_NATIVE_200_1000events.lhe.gz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def materialize() -> dict[str, object]:
    raw = gzip.open(SOURCE, "rt", encoding="utf-8").read()
    events = re.findall(r"<event>.*?</event>", raw, flags=re.DOTALL)
    if len(events) != 100:
        raise RuntimeError(f"expected 100 source events, found {len(events)}")
    first = raw.index("<event>")
    last = raw.rindex("</event>") + len("</event>")
    header = raw[:first]
    trailer = raw[last:]
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(events * 10)
    with TARGET.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as handle:
                handle.write(header + body + trailer)
    return {
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "target": str(TARGET),
        "target_sha256": sha256(TARGET),
        "source_events": len(events),
        "target_events": len(events) * 10,
        "method": "byte-preserving event-block repetition; no physics regeneration",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(materialize(), indent=2))
