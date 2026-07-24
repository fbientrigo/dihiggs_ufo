import os
import sys
import json
import hashlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path("/home/fabi/atlas_dihiggs/ufos").resolve()

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, cwd=REPO_ROOT).strip()

def get_git_output(cmd):
    return run_cmd(cmd).splitlines()

tracked_files = get_git_output("git ls-files")
untracked_files = get_git_output("git ls-files --others --exclude-standard")
all_git_status = get_git_output("git status --short")

print(f"Tracked count: {len(tracked_files)}")
print(f"Untracked count: {len(untracked_files)}")

# 1. Symlinks
symlinks = []
for root, dirs, files in os.walk(REPO_ROOT):
    if ".git" in dirs:
        dirs.remove(".git")
    for d in dirs:
        p = Path(root) / d
        if p.is_symlink():
            target = os.readlink(p)
            symlinks.append((str(p.relative_to(REPO_ROOT)), target, p.exists()))
    for f in files:
        p = Path(root) / f
        if p.is_symlink():
            target = os.readlink(p)
            symlinks.append((str(p.relative_to(REPO_ROOT)), target, p.exists()))

print(f"Symlinks found: {len(symlinks)}")

# 2. Files sizes > 5M and > 10M
files_gt_5m = []
files_gt_10m = []
file_hashes = {}
filename_map = {}

for root, dirs, files in os.walk(REPO_ROOT):
    if ".git" in dirs:
        dirs.remove(".git")
    for f in files:
        full_path = Path(root) / f
        rel_path = str(full_path.relative_to(REPO_ROOT))
        if full_path.is_symlink():
            continue
        try:
            st = full_path.stat()
            size = st.st_size
            if size > 5 * 1024 * 1024:
                files_gt_5m.append({"path": rel_path, "size_bytes": size, "size_mb": round(size / (1024*1024), 2)})
            if size > 10 * 1024 * 1024:
                files_gt_10m.append({"path": rel_path, "size_bytes": size, "size_mb": round(size / (1024*1024), 2)})
            
            # duplicate filenames
            filename_map.setdefault(f, []).append(rel_path)
            
            # SHA256 calculation for duplicates (skip files > 500MB)
            if size < 500 * 1024 * 1024:
                h = hashlib.sha256()
                with open(full_path, "rb") as fp:
                    while chunk := fp.read(65536):
                        h.update(chunk)
                sha = h.hexdigest()
                file_hashes.setdefault(sha, []).append({"path": rel_path, "size": size})
        except Exception as e:
            print(f"Error reading {rel_path}: {e}")

duplicate_filenames = {k: v for k, v in filename_map.items() if len(v) > 1}
duplicate_hashes = {k: v for k, v in file_hashes.items() if len(v) > 1}

# 3. Links & Absolute paths in docs
file_proto_links = []
abs_home_paths = []
broken_rel_links = []

markdown_files = []
json_files = []
yaml_files = []

for root, dirs, files in os.walk(REPO_ROOT):
    if ".git" in dirs:
        dirs.remove(".git")
    for f in files:
        rel_p = str((Path(root) / f).relative_to(REPO_ROOT))
        if f.endswith(".md"):
            markdown_files.append(rel_p)
        elif f.endswith(".json"):
            json_files.append(rel_p)
        elif f.endswith(".yaml") or f.endswith(".yml"):
            yaml_files.append(rel_p)

md_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

for md in markdown_files:
    md_path = REPO_ROOT / md
    try:
        content = md_path.read_text(errors='ignore')
        if 'file://' in content:
            for line_no, line in enumerate(content.splitlines(), 1):
                if 'file://' in line:
                    file_proto_links.append({"file": md, "line": line_no, "content": line.strip()})
        if '/home/fabi/' in content:
            for line_no, line in enumerate(content.splitlines(), 1):
                if '/home/fabi/' in line:
                    abs_home_paths.append({"file": md, "line": line_no, "content": line.strip()})
        
        matches = md_link_pattern.findall(content)
        for text, target in matches:
            target_clean = target.split('#')[0]
            if target_clean.startswith('http://') or target_clean.startswith('https://') or target_clean.startswith('mailto:') or target_clean.startswith('file://'):
                continue
            if not target_clean:
                continue
            target_path = (md_path.parent / target_clean).resolve()
            if not target_path.exists():
                broken_rel_links.append({"file": md, "link_text": text, "target": target, "resolved": str(target_path)})
    except Exception as e:
        print(f"Error reading md {md}: {e}")

# 4. JSON / YAML parse status
json_status = {}
for jf in json_files:
    try:
        with open(REPO_ROOT / jf, 'r') as fp:
            json.load(fp)
        json_status[jf] = "OK"
    except Exception as e:
        json_status[jf] = f"ERROR: {e}"

yaml_status = {}
try:
    import yaml
    for yf in yaml_files:
        try:
            with open(REPO_ROOT / yf, 'r') as fp:
                yaml.safe_load(fp)
            yaml_status[yf] = "OK"
        except Exception as e:
            yaml_status[yf] = f"ERROR: {e}"
except ImportError:
    yaml_status = {"YAML": "PyYAML not installed"}

# 5. Executable bit on scripts
scripts_lacking_exec = []
for root, dirs, files in os.walk(REPO_ROOT / "scripts"):
    if ".git" in dirs:
        dirs.remove(".git")
    for f in files:
        rel_p = str((Path(root) / f).relative_to(REPO_ROOT))
        full_p = Path(root) / f
        if not os.access(full_p, os.X_OK):
            scripts_lacking_exec.append(rel_p)

out_summary = {
    "head": run_cmd('git rev-parse HEAD'),
    "branch": run_cmd('git branch --show-current'),
    "tracked_count": len(tracked_files),
    "untracked_count": len(untracked_files),
    "symlinks": [{"path": s[0], "target": s[1], "exists": s[2]} for s in symlinks],
    "files_gt_5m": files_gt_5m,
    "files_gt_10m": files_gt_10m,
    "duplicate_basenames_count": len(duplicate_filenames),
    "duplicate_hashes_count": len(duplicate_hashes),
    "duplicate_filenames": duplicate_filenames,
    "duplicate_hashes": duplicate_hashes,
    "file_proto_links": file_proto_links,
    "abs_home_paths": abs_home_paths,
    "broken_rel_links": broken_rel_links,
    "json_status": json_status,
    "yaml_status": yaml_status,
    "scripts_lacking_exec": scripts_lacking_exec
}

with open("curation/repository_cleanup_20260723T081927Z/inventory_summary.json", "w") as fp:
    json.dump(out_summary, fp, indent=2)

print("Inventory JSON saved successfully.")
