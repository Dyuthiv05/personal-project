#!/usr/bin/env bash
# Run every notebook in order (outputs saved in place). Notebook 08 writes docs/story.html.
set -euo pipefail
cd "$(dirname "$0")/notebooks"
for nb in 0*.ipynb; do
  start=$(date +%s)
  ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3000 "$nb" 2>/dev/null
  echo "$nb  $(( $(date +%s) - start ))s"
done
