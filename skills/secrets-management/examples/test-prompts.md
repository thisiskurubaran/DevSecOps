# Test prompts for secrets-management

How to test: copy `skills/secrets-management` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "I accidentally pushed our Stripe live key in `config/settings.py` to GitHub an hour ago. What do I do?"
2. "Scan this repo and its history for hardcoded secrets, then help me move our `.env` values into AWS Secrets Manager with External Secrets Operator."

## Should not trigger

1. "Our CI role has `AdministratorAccess`. Help me cut it down to what the deploy job needs."
   This belongs to `cloud-iam-review`.
