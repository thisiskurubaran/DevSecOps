# Test prompts for risk-acceptance

How to test: copy `skills/risk-acceptance` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "We can't upgrade libexample to 2.x before the 30 day SLA runs out on CVE-2024-12345. Write up a risk acceptance for the pdf-import service. We have a WAF rule and a network policy in front of it."
2. "Here is an exception request from the payments team: 'Accept Checkov CKV_AWS_18, internal bucket, no expiry needed.' Should I approve it?"

## Should not trigger

1. "Semgrep flagged 40 subprocess calls in this repo. Which ones are real and which are false positives?"
   This belongs to `sast-dast-triage`.
