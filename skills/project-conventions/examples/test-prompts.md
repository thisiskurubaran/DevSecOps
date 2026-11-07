# Test prompts for project-conventions

How to test: copy `skills/project-conventions` to `~/.claude/skills/`, start a fresh Claude Code session inside a real project, and try each prompt below.

## Should trigger

1. "Write a CONVENTIONS.md for this repo covering architecture, libraries we use and things we should not do."
2. "I just joined this project. Document how things are done here so new people and reviewers follow the same rules."

## Should not trigger

1. "Write a README with install steps and a usage example for this CLI."
   This belongs to `docs-writer`.
