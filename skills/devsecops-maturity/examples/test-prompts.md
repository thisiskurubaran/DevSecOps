# Test prompts for devsecops-maturity

How to test: copy `skills/devsecops-maturity` to `~/.claude/skills/`, start a fresh Claude Code session in a repo with some CI config, and try each prompt below.

## Should trigger

1. "We are a team of eight running a payments API. Can you do an OWASP SAMM assessment of this repo and tell us what to fix over the next three quarters?"
2. "New security lead here. Look at our pipelines and settings and give me a DevSecOps maturity baseline with a short roadmap, nothing longer than five items a quarter."

## Should not trigger

1. "Threat model the new refund flow described in `docs/design/refunds.md`. What could go wrong at each trust boundary?"
   This belongs to `threat-modeling`.
