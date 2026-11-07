# Test prompts for cicd-pipeline-builder

How to test: copy `skills/cicd-pipeline-builder` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Write a GitHub Actions workflow for this Node app that runs tests, scans for secrets and vulnerable deps, builds the Docker image and deploys to AWS ECS from main."
2. "Our `.gitlab-ci.yml` uses AWS keys stored as CI variables. Switch it to OIDC and add Semgrep and Trivy stages that block the merge request on high findings."

## Should not trigger

1. "Trivy reported 140 CVEs in our image scan, which ones actually matter?"
   This belongs to `sast-dast-triage` (or `container-security` for base image fixes).
