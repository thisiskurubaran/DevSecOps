# Test prompts for observability-setup

How to test: copy `skills/observability-setup` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Add OpenTelemetry tracing and structured logging to this Express service, send it through a Collector, and make sure we never log auth headers or emails."
2. "Define an SLO for our checkout API and write Prometheus burn-rate alerts with runbook links."

## Should not trigger

1. "The API is returning 500s for everyone right now, what do we do first?"
   This belongs to `incident-response`.
