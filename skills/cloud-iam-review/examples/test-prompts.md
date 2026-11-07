# Test prompts for cloud-iam-review

How to test: copy `skills/cloud-iam-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here's the IAM policy and trust policy for our GitHub Actions deploy role. Is it too broad? Rewrite it with least privilege."
2. "Our GCP batch service account has `roles/editor` on the project. What does it actually need, and how do I find out from usage data?"

## Should not trigger

1. "This Terraform creates an S3 bucket and an RDS instance. Check it for misconfigurations."
   This belongs to `iac-review`.
