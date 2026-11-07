# Test prompts for commit-pr-writer

How to test: copy `skills/commit-pr-writer` to `~/.claude/skills/`, start a fresh Claude Code session in a repo with staged changes, and try each prompt below.

## Should trigger

1. "Write a commit message for what I have staged."
2. "I have changes in five files. Split them into sensible commits and write the PR description."

## Should not trigger

1. "Write the CHANGELOG entry and release notes for v1.4.0."
   This belongs to `docs-writer` (or `release-checklist` for the full release).
