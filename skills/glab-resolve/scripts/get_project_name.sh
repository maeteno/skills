#!/usr/bin/env bash
# Usage: get_project_name.sh
# Get current project path_with_namespace (URL-encoded for API calls)

set -euo pipefail

PROJECT=$(glab repo view --output json \
  | jq -r '.path_with_namespace' \
  | uv run python -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip(), safe=''))")

echo "$PROJECT"
