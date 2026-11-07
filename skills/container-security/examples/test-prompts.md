# Test prompts for container-security

How to test: copy `skills/container-security` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review this Dockerfile for our Python API. It's 1.2 GB and runs as root. Make it smaller and safer."
2. "Here is `trivy image myapp:1.4.0` output with 9 criticals, mostly in openssl and glibc. What should I change in the Dockerfile to fix them?"

## Should not trigger

1. "Our Deployment YAML has no securityContext or resource limits. Can you fix it?"
   This belongs to `k8s-manifest-review`.
