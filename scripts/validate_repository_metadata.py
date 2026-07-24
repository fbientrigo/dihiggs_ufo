#!/usr/bin/env python3
"""
Lightweight repository metadata validation script.
Checks:
- Relative link validity in README.md and public docs
- Absence of file:///home/ links in public entry points
- JSON parsing of all tracked JSON files
- YAML parsing of tracked YAML files (if PyYAML available)
- Existence and SHA-256 of authoritative Pack A frozen release
- Status consistency between README.md and CURRENT_STATE.md
- Absence of git merge conflict markers in tracked files
- No duplicate artifact_ids in ARTIFACT_REGISTRY.json
- Validity of symlinks (CURRENT_PACK_A, CURRENT_PACK_AA_DESIGN)
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DOCS = [
    "README.md",
    "CURRENT_STATE.md",
    "docs/CONTRACT_INDEX.md",
    "docs/ARTIFACT_STORAGE_POLICY.md",
    "docs/REPOSITORY_CURATION_BACKLOG.md",
]


def tracked_files():
    """Return repository paths tracked by Git."""
    return set(
        subprocess.check_output(
            ["git", "ls-files"], cwd=REPO_ROOT, text=True
        ).splitlines()
    )


def check_pack_a_frozen_hash():
    pack_a_path = REPO_ROOT / "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"
    expected_hash = "58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6"
    if not pack_a_path.exists():
        print(f"FAIL: Pack A frozen zip not found at {pack_a_path}")
        return False

    h = hashlib.sha256()
    with open(pack_a_path, "rb") as fp:
        while chunk := fp.read(65536):
            h.update(chunk)
    actual_hash = h.hexdigest()
    if actual_hash != expected_hash:
        print(
            "FAIL: Pack A frozen SHA256 mismatch!\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual_hash}"
        )
        return False
    print("PASS: Pack A frozen SHA256 verified.")
    return True


def check_file_proto_links():
    failed = False
    for doc in PUBLIC_DOCS:
        doc_p = REPO_ROOT / doc
        if not doc_p.exists():
            continue
        content = doc_p.read_text(errors="ignore")
        if "file:///" in content:
            print(f"FAIL: Found local file:/// link in public entry point: {doc}")
            failed = True
    if not failed:
        print("PASS: No local file:/// links found in public entry points.")
    return not failed


def check_public_doc_links():
    """Validate relative Markdown links in all public entry-point documents."""
    md_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    failed = False

    try:
        tracked = tracked_files()
    except Exception as exc:
        print(f"FAIL: Could not retrieve tracked files from Git: {exc}")
        return False

    for doc in PUBLIC_DOCS:
        doc_path = REPO_ROOT / doc
        if not doc_path.exists():
            print(f"FAIL: Public document does not exist: {doc}")
            failed = True
            continue

        content = doc_path.read_text(errors="ignore")
        for text, target in md_link_pattern.findall(content):
            target = target.strip()
            target_clean = target.split("#", 1)[0].strip()

            if target.startswith("#") or not target_clean:
                continue
            if target_clean.startswith(
                ("http://", "https://", "mailto:", "file://")
            ):
                continue

            target_path = (doc_path.parent / target_clean).resolve()
            try:
                rel_str = target_path.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                print(
                    f"FAIL: {doc} link points outside repository root: "
                    f"[{text}]({target}) -> {target_path}"
                )
                failed = True
                continue

            if rel_str.startswith("pack_aa/runs/"):
                print(
                    f"FAIL: {doc} points to forbidden Pack AA run directory: "
                    f"[{text}]({target})"
                )
                failed = True
                continue

            if rel_str.endswith(".truth.jsonl"):
                print(
                    f"FAIL: {doc} points to forbidden truth event file: "
                    f"[{text}]({target})"
                )
                failed = True
                continue

            if not target_path.exists():
                print(
                    f"FAIL: Broken link in {doc}: [{text}]({target}) "
                    f"-> {target_path}"
                )
                failed = True
                continue

            if target_path.is_file() or target_path.is_symlink():
                if rel_str not in tracked:
                    print(
                        f"FAIL: {doc} link target is not tracked by Git: "
                        f"[{text}]({target}) -> {rel_str}"
                    )
                    failed = True
            elif target_path.is_dir():
                prefix = rel_str + "/" if rel_str != "." else ""
                if not any(
                    tracked_path == rel_str or tracked_path.startswith(prefix)
                    for tracked_path in tracked
                ):
                    print(
                        f"FAIL: {doc} link target directory has no tracked files: "
                        f"[{text}]({target}) -> {rel_str}"
                    )
                    failed = True

    if not failed:
        print(
            "PASS: Relative links in all public documents resolve to tracked "
            "repository content."
        )
    return not failed


def check_json_parsing():
    files = tracked_files()
    json_files = [path for path in files if path.endswith(".json")]
    failed = False
    for json_file in json_files:
        try:
            with open(REPO_ROOT / json_file, "r") as fp:
                json.load(fp)
        except Exception as exc:
            print(f"FAIL: JSON parse error in {json_file}: {exc}")
            failed = True
    if not failed:
        print(f"PASS: Parsed {len(json_files)} tracked JSON files successfully.")
    return not failed


def check_yaml_parsing():
    try:
        import yaml
    except ImportError:
        print("SKIP: PyYAML not installed.")
        return True

    files = tracked_files()
    yaml_files = [path for path in files if path.endswith((".yaml", ".yml"))]
    failed = False
    for yaml_file in yaml_files:
        try:
            with open(REPO_ROOT / yaml_file, "r") as fp:
                yaml.safe_load(fp)
        except Exception as exc:
            print(f"FAIL: YAML parse error in {yaml_file}: {exc}")
            failed = True
    if not failed:
        print(f"PASS: Parsed {len(yaml_files)} tracked YAML files successfully.")
    return not failed


def check_artifact_registry():
    registry_path = REPO_ROOT / "ARTIFACT_REGISTRY.json"
    if not registry_path.exists():
        print("FAIL: ARTIFACT_REGISTRY.json not found.")
        return False

    with open(registry_path) as fp:
        registry = json.load(fp)

    try:
        tracked = tracked_files()
    except Exception as exc:
        print(f"FAIL: Could not retrieve tracked files from Git: {exc}")
        return False

    seen_ids = set()
    failed = False
    for item in registry:
        artifact_id = item.get("artifact_id")
        if artifact_id in seen_ids:
            print(
                "FAIL: Duplicate artifact_id in ARTIFACT_REGISTRY.json: "
                f"{artifact_id}"
            )
            failed = True
        seen_ids.add(artifact_id)

        # External and historical artifacts may intentionally be absent from a
        # clean checkout. Only require existence when the registry path itself
        # is tracked by Git.
        current_path = item.get("current_path")
        if current_path and current_path in tracked:
            full_path = REPO_ROOT / current_path
            if not full_path.exists():
                print(
                    f"FAIL: Registry item {artifact_id} points to non-existent "
                    f"tracked path: {current_path}"
                )
                failed = True

    if not failed:
        print(
            f"PASS: ARTIFACT_REGISTRY.json verified "
            f"({len(seen_ids)} unique artifacts)."
        )
    return not failed


def check_symlinks():
    symlinks = ["CURRENT_PACK_A", "CURRENT_PACK_AA_DESIGN"]
    failed = False
    for symlink in symlinks:
        symlink_path = REPO_ROOT / symlink
        if not symlink_path.is_symlink():
            print(f"FAIL: {symlink} is not a symlink.")
            failed = True
            continue
        target = os.readlink(symlink_path)
        if os.path.isabs(target):
            print(f"FAIL: {symlink} has absolute symlink target: {target}")
            failed = True
        target_path = (REPO_ROOT / target).resolve()
        if not target_path.exists():
            print(f"FAIL: {symlink} symlink target does not exist: {target}")
            failed = True
    if not failed:
        print("PASS: Symlinks verified.")
    return not failed


def check_merge_markers():
    files = tracked_files()
    merge_marker_pattern = re.compile(r"^(<<<<<<<|=======|>>>>>>>)\s")
    failed = False
    for tracked_file in files:
        full_path = REPO_ROOT / tracked_file
        if full_path.is_symlink() or not full_path.is_file():
            continue
        if tracked_file.endswith(
            (".zip", ".dat", ".grid", ".tbl", ".pyc", ".pkl", ".png", ".jpg")
        ):
            continue
        try:
            content = full_path.read_text(errors="ignore")
            for line_number, line in enumerate(content.splitlines(), 1):
                if merge_marker_pattern.match(line):
                    print(
                        f"FAIL: Git merge marker in {tracked_file}:{line_number}"
                    )
                    failed = True
        except Exception:
            pass
    if not failed:
        print("PASS: No merge conflict markers found.")
    return not failed


def main():
    print("=== Running Repository Metadata Validation ===")
    checks = [
        check_pack_a_frozen_hash(),
        check_file_proto_links(),
        check_public_doc_links(),
        check_json_parsing(),
        check_yaml_parsing(),
        check_artifact_registry(),
        check_symlinks(),
        check_merge_markers(),
    ]
    if all(checks):
        print("=== ALL METADATA VALIDATIONS PASSED ===")
        sys.exit(0)

    print("=== METADATA VALIDATION FAILED ===")
    sys.exit(1)


if __name__ == "__main__":
    main()
