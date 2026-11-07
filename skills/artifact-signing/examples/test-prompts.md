# Test prompts for artifact-signing

How to test: copy `skills/artifact-signing` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Add cosign keyless signing and SLSA provenance to our GitHub Actions release workflow that pushes to GHCR, and give me a Kyverno policy so the cluster only runs images signed by that workflow."
2. "`cosign verify` fails with 'none of the expected identities matched' on an image our release job just signed. Here is the workflow and the command I ran."

## Should not trigger

1. "Here is our CycloneDX SBOM and the Grype output. Which of these CVEs in our npm dependencies do we need to fix first?"
   This belongs to `dependency-supply-chain`.
