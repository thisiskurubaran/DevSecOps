# Test prompts for pipeline-hardening

How to test: copy `skills/pipeline-hardening` to `~/.claude/skills/`, start a fresh Claude Code session in a repo that has a `.github/workflows/` folder, and try each prompt below.

## Should trigger

1. "Audit the workflows in `.github/workflows/` for security problems. We use `pull_request_target` for the labeler and a self-hosted runner for integration tests."
2. "zizmor reports 14 findings on our repo, mostly `template-injection` and `unpinned-uses`. Which ones matter and what is the fixed YAML?"

## Should not trigger

1. "Write a GitHub Actions workflow for our Go service that runs tests, Semgrep and Trivy, then deploys to ECS."
   This belongs to `cicd-pipeline-builder`.
