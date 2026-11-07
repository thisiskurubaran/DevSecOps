# Test prompts for vuln-management

How to test: copy `skills/vuln-management` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below. For the script, export findings from DefectDojo or your tracker as CSV and run `python3 scripts/sla_report.py findings.csv`.

## Should trigger

1. "We get findings from Trivy, Snyk and Dependabot plus Semgrep and CodeQL. Help me set remediation SLAs by severity and a way to stop counting the same CVE three times."
2. "Here's a CSV export from DefectDojo. Which findings are past SLA, who owns them, and what's our MTTR for highs this quarter?"

## Should not trigger

1. "Semgrep flagged 40 issues on this PR. Which ones are real and which are false positives?"
   This belongs to `sast-dast-triage`.
