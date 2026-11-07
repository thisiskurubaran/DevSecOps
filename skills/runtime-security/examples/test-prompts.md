# Test prompts for runtime-security

How to test: copy `skills/runtime-security` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Falco keeps firing 'Terminal shell in container' for our debug toolbox pods in the `debug` namespace. How do I quiet it without turning the rule off?"
2. "Got this Falco alert at 3am: `Sensitive file read ... proc=python3 file=/etc/shadow image=registry.example.com/web:2.1`. Is this an incident?"

## Should not trigger

1. "Review this Deployment YAML. Is it missing securityContext settings or resource limits?"
   This belongs to `k8s-manifest-review`.
