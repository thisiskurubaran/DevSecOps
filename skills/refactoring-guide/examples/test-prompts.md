# Test prompts for refactoring-guide

How to test: copy `skills/refactoring-guide` to `~/.claude/skills/`, start a fresh Claude Code session in a project with a test suite, and try each prompt.

## Should trigger

1. "`checkout.py` has a 300-line `process_payment` function. Split it up without changing behavior."
2. "Rename `UserManager` to `AccountService` everywhere and move it into `src/accounts/`. Keep the tests passing."

## Should not trigger

1. "Review my PR diff and tell me what's wrong, ranked by severity." This belongs to `code-review`.
