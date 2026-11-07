# Test prompts for dast-setup

How to test: copy `skills/dast-setup` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Add an OWASP ZAP scan to our GitHub Actions. Every PR gets a preview at pr-<number>.preview.example.com, and I want it to fail only on new high findings."
2. "Write a ZAP Automation Framework plan that logs in with a test account and runs an active scan against staging every night, without hitting logout or the delete account endpoint."

## Should not trigger

1. "ZAP gave us 40 alerts on staging. Which ones are real and which are false positives?"
   This belongs to `sast-dast-triage`.
