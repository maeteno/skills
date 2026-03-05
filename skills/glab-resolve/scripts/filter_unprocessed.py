#!/usr/bin/env python3
# Usage: filter_unprocessed.py <DISCUSSIONS_JSON | ->
# Filter unresolved human review discussion threads from GitLab MR discussions API
# Input: JSON array of discussions from GitLab MR /discussions endpoint
# Output: Simplified JSON of unresolved diff discussion threads

import sys
import json


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <DISCUSSIONS_JSON | ->", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    if input_file == "-":
        discussions = json.load(sys.stdin)
    else:
        with open(input_file, 'r') as f:
            discussions = json.load(f)

    unresolved = []
    for discussion in discussions:
        notes = discussion.get("notes", [])
        if not notes:
            continue

        first_note = notes[0]

        # Only human-resolvable diff discussion threads
        if first_note.get("type") != "DiffNote":
            continue
        if not first_note.get("resolvable"):
            continue
        if first_note.get("resolved", False):
            continue

        replies = [
            {"author": n["author"]["name"], "comment": n["body"]}
            for n in notes[1:]
        ]

        unresolved.append({
            "discussion_id": discussion["id"],
            "author": first_note["author"]["name"],
            "comment": first_note["body"],
            "position": first_note.get("position", {}),
            "replies": replies,
        })

    print(json.dumps(unresolved, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
