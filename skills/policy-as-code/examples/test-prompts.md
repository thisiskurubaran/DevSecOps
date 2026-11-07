# Test prompts for policy-as-code

How to test: copy `skills/policy-as-code` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Write a conftest Rego policy that fails our Terraform plan if any RDS instance is publicly accessible or unencrypted, with unit tests."
2. "We need a Kyverno policy that only allows images from registry.example.com, in audit mode first. Also map it to SOC 2 and PCI controls for the auditors."

## Should not trigger

1. "Review these Kubernetes manifests and tell me what is insecure."
   This belongs to `k8s-manifest-review`.
