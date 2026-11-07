# Test prompts for iac-review

How to test: copy `skills/iac-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review the Terraform in `infra/` before I merge. It adds an S3 bucket, an RDS Postgres instance and a security group."
2. "Checkov flagged 23 issues on this CloudFormation template. Which ones are real and how do I fix them in the YAML?"

## Should not trigger

1. "Is this IAM policy too broad? It gives our Lambda `s3:*` and `dynamodb:*` on all resources."
   This belongs to `cloud-iam-review`.
