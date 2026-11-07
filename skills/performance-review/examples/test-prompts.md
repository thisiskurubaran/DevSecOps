# Test prompts for performance-review

How to test: copy `skills/performance-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt.

## Should trigger

1. "The `/api/orders` endpoint takes 3 seconds and I see about 200 SQL queries in the logs for one request. Can you find out why?"
2. "Here's an EXPLAIN ANALYZE output and our React dashboard re-renders constantly when the price feed ticks. What's slow and how do I fix it?"

## Should not trigger

1. "Set up OpenTelemetry tracing and a latency SLO alert for our checkout service." This belongs to `observability-setup`.
