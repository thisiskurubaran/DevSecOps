# Test prompts for dependency-supply-chain

How to test: copy `skills/dependency-supply-chain` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is our `npm audit --json` output. Which of these CVEs actually affect us and what is the safest upgrade path?"
2. "A customer wants a CycloneDX SBOM and a license report for our Python service. Generate both and flag any GPL or AGPL packages."

## Should not trigger

1. "Trivy found 60 CVEs in our `node:18` base image. Help me harden the Dockerfile."
   This belongs to `container-security`.
