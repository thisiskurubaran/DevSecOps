# Test prompts for security-headers

How to test: copy `skills/security-headers` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is the `curl -I` output from our app. Mozilla Observatory gives it a D. What headers are missing and how do I add them in nginx?"
2. "I want to add a Content-Security-Policy to our Next.js app without breaking the analytics script. Should I use nonces or hashes, and how do I roll it out?"

## Should not trigger

1. "Our refresh tokens never expire and we store the JWT in localStorage. Is that a problem?"
   This belongs to `auth-review`.
