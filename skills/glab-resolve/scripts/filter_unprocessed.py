#!/usr/bin/env python3
# Usage: filter_unprocessed.py <DISCUSSIONS_JSON>
# Filter unresolved human review comments from GitLab MR notes
# Input: JSON array of notes from GitLab MR (e.g. from glab api)
# Output: Simplified JSON of unresolved diff comments

import sys
import json


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <DISCUSSIONS_JSON>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    if input_file == "-":
        notes = json.load(sys.stdin)
    else:
        with open(input_file, 'r') as f:
            notes = json.load(f)

    unresolved = []
    for note in notes:
        # Only human-resolvable diff comments
        if note.get("type") != "DiffNote":
            continue
        if not note.get("resolvable"):
            continue
        if note.get("resolved", False):
            continue

        pos = note.get("position", {})
        unresolved.append({
            "id": note["id"],
            "resolvable": note.get("resolvable", False),
            "resolved": note.get("resolved", False),
            "author": note["author"]["name"],
            "comment": note["body"],
            "position": pos,
        })

    print(json.dumps(unresolved, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
