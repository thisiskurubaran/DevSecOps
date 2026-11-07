# Test prompts for cspm-triage

How to test: copy `skills/cspm-triage` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "I ran `prowler aws --compliance cis_3.0_aws` on our prod account and got 300 failures. Here is the CSV. What should we fix first?"
2. "Security Hub shows 900 failed controls across 12 accounts. Help me turn this export into a plan with owners, and tell me which ones to suppress."

## Should not trigger

1. "Review this Terraform module before I merge. It creates an S3 bucket and a security group."
   This belongs to `iac-review`.
