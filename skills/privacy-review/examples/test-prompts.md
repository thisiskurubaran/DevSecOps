# Test prompts for privacy-review

How to test: copy `skills/privacy-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "This PR adds date of birth, phone number and a Segment `identify` call to sign-up. Can you do a privacy review and build a data inventory for the user model?"
2. "We got a GDPR deletion request. Walk through our codebase and tell me every place this user's data lives that `delete_account()` misses, including Elasticsearch and backups."

## Should not trigger

1. "Our structured logs include full request bodies with emails. Set up a Fluent Bit filter to redact them before they reach Loki."
   This belongs to `observability-setup`.
