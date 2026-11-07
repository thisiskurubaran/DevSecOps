# Test prompts for debugging-playbook

How to test: copy `skills/debugging-playbook` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is the stack trace: `TypeError: Cannot read properties of undefined (reading 'id')` in checkout.ts:54. Fix it."
2. "`test_sync_orders` passes locally but fails about one run in ten in CI. Figure out why."

## Should not trigger

1. "Write unit tests for the `slugify` helper, it has none."
   This belongs to `test-generator`.
