# Test prompts for api-scaffolder

How to test: copy `skills/api-scaffolder` to `~/.claude/skills/`, start a fresh Claude Code session in a project with a few existing endpoints, and try each prompt.

## Should trigger

1. "Add a `POST /api/v1/invoices` endpoint that creates an invoice for the logged-in user. Follow how the orders routes are done."
2. "Scaffold CRUD routes for a `Project` resource in our FastAPI app, with pydantic models, tests and the OpenAPI entries."

## Should not trigger

1. "Review our `/users` endpoints for IDOR and injection problems." This belongs to `security-audit`.
