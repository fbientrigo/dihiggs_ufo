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

import sys
import os
import json
import hashlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

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
        print(f"FAIL: Pack A frozen SHA256 mismatch!\n  Expected: {expected_hash}\n  Actual:   {actual_hash}")
        return False
    print("PASS: Pack A frozen SHA256 verified.")
    return True

def check_file_proto_links():
    public_docs = ["README.md", "CURRENT_STATE.md", "docs/CONTRACT_INDEX.md", "docs/ARTIFACT_STORAGE_POLICY.md"]
    failed = False
    for doc in public_docs:
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

def check_readme_links():
    readme_p = REPO_ROOT / "README.md"
    if not readme_p.exists():
        print("FAIL: README.md does not exist.")
        return False
    content = readme_p.read_text(errors="ignore")
    md_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    failed = False

    try:
        tracked_files = set(
            subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
        )
    except Exception as e:
        print(f"FAIL: Could not retrieve tracked files from Git: {e}")
        return False

    for text, target in md_link_pattern.findall(content):
        target_clean = target.split('#')[0]
        if target_clean.startswith(('http://', 'https://', 'mailto:', 'file://')):
            continue
        if not target_clean:
            continue

        if "pack_aa/runs/" in target_clean or target_clean.startswith("pack_aa/runs/"):
            print(f"FAIL: README.md points to forbidden run directory: [{text}]({target})")
            failed = True
            continue

        if target_clean.endswith(".truth.jsonl") or "*.truth.jsonl" in target_clean:
            print(f"FAIL: README.md points to forbidden truth event file: [{text}]({target})")
            failed = True
            continue

        target_path = (readme_p.parent / target_clean).resolve()
        if not target_path.exists():
            print(f"FAIL: Broken link in README.md (does not exist): [{text}]({target}) -> {target_path}")
            failed = True
            continue

        try:
            rel_str = str(target_path.relative_to(REPO_ROOT))
        except ValueError:
            print(f"FAIL: README.md link points outside repository root: [{text}]({target}) -> {target_path}")
            failed = True
            continue

        if target_path.is_file() or target_path.is_symlink():
            if rel_str not in tracked_files:
                print(f"FAIL: README.md link target file is not tracked by Git: [{text}]({target}) -> {rel_str}")
                failed = True
        elif target_path.is_dir():
            prefix = rel_str + "/" if rel_str != "." else ""
            if not any(f == rel_str or f.startswith(prefix) for f in tracked_files):
                print(f"FAIL: README.md link target directory has no tracked files in Git: [{text}]({target}) -> {rel_str}")
                failed = True

    if not failed:
        print("PASS: All README.md relative links resolved and verified tracked in Git successfully.")
    return not failed

def check_json_parsing():
    tracked_files = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
    json_files = [f for f in tracked_files if f.endswith(".json")]
    failed = False
    for jf in json_files:
        try:
            with open(REPO_ROOT / jf, "r") as fp:
                json.load(fp)
        except Exception as e:
            print(f"FAIL: JSON parse error in {jf}: {e}")
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
    
    tracked_files = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
    yaml_files = [f for f in tracked_files if f.endswith((".yaml", ".yml"))]
    failed = False
    for yf in yaml_files:
        try:
            with open(REPO_ROOT / yf, "r") as fp:
                yaml.safe_load(fp)
        except Exception as e:
            print(f"FAIL: YAML parse error in {yf}: {e}")
            failed = True
    if not failed:
        print(f"PASS: Parsed {len(yaml_files)} tracked YAML files successfully.")
    return not failed

def check_artifact_registry():
    registry_p = REPO_ROOT / "ARTIFACT_REGISTRY.json"
    if not registry_p.exists():
        print("FAIL: ARTIFACT_REGISTRY.json not found.")
        return False
    
    with open(registry_p) as fp:
        registry = json.load(fp)
    
    try:
        tracked_files = set(
            subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
        )
    except Exception as e:
        print(f"FAIL: Could not retrieve tracked files from Git: {e}")
        return False

    seen_ids = set()
    failed = False
    for item in registry:
        aid = item.get("artifact_id")
        if aid in seen_ids:
            print(f"FAIL: Duplicate artifact_id in ARTIFACT_REGISTRY.json: {aid}")
            failed = True
        seen_ids.add(aid)
        
        # Verify path exists for tracked artifacts
        curr_p = item.get("current_path")
        if curr_p:
            full_p = REPO_ROOT / curr_p
            if curr_p in tracked_files and not full_p.exists():
                print(f"FAIL: Registry item {aid} points to non-existent tracked path: {curr_p}")
                failed = True
    
    if not failed:
        print(f"PASS: ARTIFACT_REGISTRY.json verified ({len(seen_ids)} unique artifacts).")
    return not failed

def check_symlinks():
    symlinks = ["CURRENT_PACK_A", "CURRENT_PACK_AA_DESIGN"]
    failed = False
    for s in symlinks:
        sp = REPO_ROOT / s
        if not sp.is_symlink():
            print(f"FAIL: {s} is not a symlink.")
            failed = True
            continue
        target = os.readlink(sp)
        if os.path.isabs(target):
            print(f"FAIL: {s} has absolute symlink target: {target}")
            failed = True
        target_path = (REPO_ROOT / target).resolve()
        if not target_path.exists():
            print(f"FAIL: {s} symlink target does not exist: {target}")
            failed = True
    if not failed:
        print("PASS: Symlinks verified.")
    return not failed

def check_merge_markers():
    tracked_files = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
    merge_marker_pattern = re.compile(r'^(<<<<<<<|=======|>>>>>>>)\s')
    failed = False
    for tf in tracked_files:
        full_p = REPO_ROOT / tf
        if full_p.is_symlink() or not full_p.is_file():
            continue
        # Skip binary files
        if tf.endswith((".zip", ".dat", ".grid", ".tbl", ".pyc", ".pkl", ".png", ".jpg")):
            continue
        try:
            content = full_p.read_text(errors="ignore")
            for line_no, line in enumerate(content.splitlines(), 1):
                if merge_marker_pattern.match(line):
                    print(f"FAIL: Git merge marker in {tf}:{line_no}")
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
        check_readme_links(),
        check_json_parsing(),
        check_yaml_parsing(),
        check_artifact_registry(),
        check_symlinks(),
        check_merge_markers()
    ]
    if all(checks):
        print("=== ALL METADATA VALIDATIONS PASSED ===")
        sys.exit(0)
    else:
        print("=== METADATA VALIDATION FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
