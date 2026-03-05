#!/usr/bin/env bash
# Usage: fetch_discussions.sh <MR_ID>
# Fetch unprocessed discussion threads for a GitLab MR by combining other scripts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MR_ID="${1:?Usage: $0 <MR_ID>}"

PROJECT=$("$SCRIPT_DIR/get_project_name.sh")

echo "Fetching unprocessed discussions for MR ${MR_ID} ..." >&2

# Fetch all comments and filter unprocessed
glab api --paginate "projects/${PROJECT}/merge_requests/${MR_ID}/notes" | uv run "$SCRIPT_DIR/filter_unprocessed.py" -
