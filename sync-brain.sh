#!/usr/bin/env bash
set -euo pipefail

NOTES_DIR="${NOTES_DIR:-$HOME/notes}"

cd "$NOTES_DIR"
git add -A
git diff --cached --quiet && exit 0
git commit -m "brain sync $(date -Is)"
git push