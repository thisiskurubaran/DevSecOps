# Test prompts for migration-helper

How to test: copy `skills/migration-helper` to `~/.claude/skills/`, start a fresh Claude Code session in a project with a migrations folder, and try each prompt.

## Should trigger

1. "Write an Alembic migration that makes `users.email` NOT NULL and unique. The table has about 30 million rows and we can't take downtime."
2. "Is this Rails migration safe to run in production? It renames `orders.total` to `orders.amount_cents`."

## Should not trigger

1. "Our `/orders` page is slow and I think we're missing an index, can you find out why?" This belongs to `performance-review`.
