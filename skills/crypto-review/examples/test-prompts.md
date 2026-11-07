# Test prompts for crypto-review

How to test: copy `skills/crypto-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review `app/crypto.py` before I merge. It encrypts customer notes with AES-CBC and a key from settings, and generates invite codes with `random.choice`."
2. "Our Go service sets `InsecureSkipVerify: true` to talk to an internal API and still allows TLS 1.0. What should the `tls.Config` look like?"

## Should not trigger

1. "Check our OAuth login flow. Are we validating the ID token and rotating refresh tokens correctly?"
   This belongs to `auth-review`.
