#!/usr/bin/env bash
# ROLLBACK_WORKSPACE_LAYOUT.sh
# Restores the original workspace layout using PATH_MIGRATION.tsv

set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)

if [[ "${1:-}" != "--confirm" ]]; then
    echo "Usage: $0 --confirm"
    echo "This script will roll back all file relocations according to PATH_MIGRATION.tsv."
    exit 1
fi

echo "Starting layout rollback..."

TSV="$ROOT/PATH_MIGRATION.tsv"
if [[ ! -f "$TSV" ]]; then
    echo "Error: PATH_MIGRATION.tsv not found!" >&2
    exit 2
fi

# Read the TSV file line by line, skipping the header
tail -n +2 "$TSV" | while IFS=$'	' read -r old_path new_path sha256_before sha256_after classification compatibility_pointer; do
    # Skip symlinks if they don't have checksum
    if [[ "$classification" == "SYMLINK" ]]; then
        src="$ROOT/$new_path"
        dst="$ROOT/$old_path"
        if [[ -L "$src" ]]; then
            # Verify target directory for rollback exists
            mkdir -p "$(dirname "$dst")"
            # Re-create symlink at original path
            target=$(readlink "$src")
            ln -sf "$target" "$dst"
            rm -f "$src"
            echo "Restored symlink: $old_path"
        fi
        continue
    fi
    
    src="$ROOT/$new_path"
    dst="$ROOT/$old_path"
    
    # Verify source file exists
    if [[ ! -f "$src" ]]; then
        echo "Error: Source file does not exist during rollback: $new_path" >&2
        exit 3
    fi
    
    # Verify source file hash matches sha256_after
    computed_after=$(sha256sum "$src" | cut -d' ' -f1)
    if [[ "$computed_after" != "$sha256_after" ]]; then
        echo "Error: Hash mismatch for source file $new_path before rollback!" >&2
        echo "Expected: $sha256_after, Got: $computed_after" >&2
        exit 4
    fi
    
    # Verify destination file does NOT exist
    if [[ -f "$dst" ]]; then
        echo "Error: Destination file already exists: $old_path" >&2
        exit 5
    fi
    
    # Create destination directory
    mkdir -p "$(dirname "$dst")"
    
    # Move file
    cp -p "$src" "$dst"
    
    # Verify destination file hash matches sha256_before
    computed_before=$(sha256sum "$dst" | cut -d' ' -f1)
    if [[ "$computed_before" != "$sha256_before" ]]; then
        echo "Error: Hash mismatch for destination file $old_path after rollback!" >&2
        echo "Expected: $sha256_before, Got: $computed_before" >&2
        exit 6
    fi
    
    # Remove relocated file
    rm -f "$src"
    echo "Restored: $old_path"
done

# Clean up symlinks at the root
rm -f "$ROOT/CURRENT_PACK_A"
rm -f "$ROOT/CURRENT_PACK_AA_DESIGN"

# Clean up empty directories recursively (but do not delete directories with unknown files)
find "$ROOT/releases" "$ROOT/design" "$ROOT/evidence" "$ROOT/inputs" "$ROOT/logs" "$ROOT/scripts" "$ROOT/archive" -type d -empty -delete 2>/dev/null || true

echo "Rollback completed successfully."
