# Test prompts for api-security-review

How to test: copy `skills/api-security-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is our `openapi.yaml` for the orders service. Check it against the OWASP API Top 10 and tell me what Spectral would flag."
2. "Review this GraphQL server setup and the `Order` resolvers. Can one user query another user's orders, and do we need depth limits?"

## Should not trigger

1. "Add a `POST /invoices` endpoint with request validation, tests and OpenAPI docs, following our existing controller layout."
   This belongs to `api-scaffolder`.
