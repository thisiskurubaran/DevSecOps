# Test prompts for release-checklist

How to test: copy `skills/release-checklist` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "We're tagging v2.3.0 tomorrow. It has a new orders column migration and a checkout redesign behind a flag. Give me a go/no-go checklist and a rollback plan."
2. "Are we ready to ship this Helm chart change to prod? Here is the diff since the last tag."

## Should not trigger

1. "Write a GitHub Actions workflow that builds and pushes our Docker image."
   This belongs to `cicd-pipeline-builder`.
