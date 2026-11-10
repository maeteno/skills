---
name: git-commit
description: Generate well-structured, descriptive git commit messages following conventional commit standards. Use when the user wants to commit changes, asks for help writing commit messages, or invokes /commit. Analyzes staged/unstaged changes and produces clear, informative commit messages.
---

# Git Commit

Generate conventional commit messages. Present the message for user confirmation before running `git commit`.

## Workflow

1. Run in parallel: `git status` and `git diff --cached`.
   - If nothing is staged, ask whether to stage all or specific files.
   - If you already know the changes from the current conversation context, skip re-reading diffs.
2. Compose the message (format below) and present it to the user. Do NOT run `git commit` until the user explicitly confirms.

Skip `git log` unless the repository's commit style is unknown to you.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- `scope`, `body`, `footer` are optional; include them only when they add value
- Subject: imperative mood, no trailing period, under 72 characters
- Body: explain **what** and **why**, not how; wrap at 72 chars
- Footer: `Closes #123` / `BREAKING CHANGE: description`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `merge`, `revert`.

## Rules

- Never generate vague messages (`Fix bug`, `Update code`, `WIP`, `Minor changes`)
- One purpose per commit; suggest splitting mixed changes
- English by default; use Chinese only if the user explicitly requests it
- No AI attribution of any kind

## Examples

```
feat(auth): add OAuth2 login support
```

```
fix(cart): resolve incorrect total when removing items

The cart total was not recalculated after removing an item due to
a stale cache. Clear the price cache before recalculating totals.

Closes #234
```
