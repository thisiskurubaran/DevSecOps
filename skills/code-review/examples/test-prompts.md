# Test prompts for code-review

How to test: copy `skills/code-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review PR #128 before I merge it. Rank anything you find by severity."
2. "Here is my staged diff for the orders endpoint. Anything wrong with it?"

## Should not trigger

1. "Run a full OWASP Top 10 audit on our login and session handling code."
   This belongs to `security-audit`.
