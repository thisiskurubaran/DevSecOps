# Test prompts for test-generator

How to test: copy `skills/test-generator` to `~/.claude/skills/`, start a fresh Claude Code session in a project with an existing test suite, and try each prompt below.

## Should trigger

1. "Write pytest tests for `parse_invoice()` in billing/invoices.py, including edge cases."
2. "Coverage on src/orders is low. Add unit and integration tests for the order service."

## Should not trigger

1. "Checkout returns a 500 for some users since yesterday. Find out why and fix it."
   This belongs to `debugging-playbook`.
