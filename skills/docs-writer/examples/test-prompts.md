# Test prompts for docs-writer

How to test: copy `skills/docs-writer` to `~/.claude/skills/`, start a fresh Claude Code session in a real project, and try each prompt.

## Should trigger

1. "Our README still says to run `python setup.py install`. Rewrite it so a new dev can get the app running from a clean clone."
2. "Write an ADR for switching our background jobs from Celery to Postgres-backed queues, and add Google-style docstrings to `jobs/queue.py`."

## Should not trigger

1. "Write a commit message and PR description for my staged changes." This belongs to `commit-pr-writer`.
