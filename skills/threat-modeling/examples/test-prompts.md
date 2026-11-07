# Test prompts for threat-modeling

How to test: copy `skills/threat-modeling` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is the design doc for our new file sharing feature with public links. Threat model it with STRIDE before we start building."
2. "We are adding a Stripe webhook that updates customer plans and a worker that renders invoices to S3. What could go wrong security-wise in this architecture?"

## Should not trigger

1. "Scan `src/auth/` for SQL injection and broken access control."
   This belongs to `security-audit`.
