# Test prompts for security-audit

How to test: copy `skills/security-audit` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Do an OWASP Top 10 audit of the `api/` folder. Focus on injection and broken access control."
2. "Is our password reset flow in `auth/reset.ts` safe? Check tokens, expiry and session handling."

## Should not trigger

1. "Semgrep gave us 340 findings on the last run. Which ones are real?"
   This belongs to `sast-dast-triage`.
