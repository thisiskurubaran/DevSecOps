# Test prompts for auth-review

How to test: copy `skills/auth-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here's our Express JWT middleware and the refresh token endpoint. Are we validating tokens correctly, and do we handle refresh token reuse?"
2. "Review the OIDC login in `src/auth/`. We use Keycloak, the SPA does the callback, and I'm not sure we check state or nonce."

## Should not trigger

1. "This AWS role trust policy lets our CI assume it. Is `sts:AssumeRole` with `Principal: *` and an external ID condition too open?"
   This belongs to `cloud-iam-review`.
