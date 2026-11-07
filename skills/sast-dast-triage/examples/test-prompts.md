# Test prompts for sast-dast-triage

How to test: copy `skills/sast-dast-triage` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is `semgrep.sarif` from last night's run with 180 results. Tell me which are real and what to fix first."
2. "ZAP baseline flagged 25 alerts on staging. Sort out the false positives and write the ignore config for them."

## Should not trigger

1. "Dependabot opened 14 alerts for lodash and axios CVEs. Which upgrades matter?"
   This belongs to `dependency-supply-chain`.
