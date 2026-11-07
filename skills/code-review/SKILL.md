---
name: code-review
description: Review a diff or pull request against team standards and rank findings by severity (blocker, major, minor, nit) with file, line and a concrete fix. Use when the user asks to review a PR, a branch, a patch, staged changes, or "look over this code" before merge.
---

# Code Review

Review a change the way a careful senior teammate would: read the diff in context, find what will break or hurt later, and say exactly how to fix it. Rank everything so the author knows what blocks the merge and what is taste.

## When to use

- The user shares a diff, a PR link or number, a branch name, or says "review my staged changes".
- The user pastes a function or file and asks "anything wrong with this?" before merging.
- A PR touches application code and nobody has reviewed it yet.

Not for: deep OWASP or auth audits (use `security-audit`), sorting scanner output (use `sast-dast-triage`), query and memory hot spots (use `performance-review`), Terraform or Kubernetes files (use `iac-review` or `k8s-manifest-review`), or restructuring code without a bug (use `refactoring-guide`).

## Steps

1. Get the change. Prefer the real diff over a pasted snippet:
   - Local: `git diff --merge-base origin/main` or `git diff --staged`.
   - GitHub: `gh pr diff <number>` and `gh pr view <number> --json title,body,files`.
2. Read the PR title, description and linked issue. Write one sentence on what the change is supposed to do. If you cannot, ask before reviewing.
3. Find the team standards. Check, in order: `CONVENTIONS.md` or `docs/conventions.md` (see the `project-conventions` skill), `CONTRIBUTING.md`, lint configs (`.eslintrc*`, `ruff.toml`, `pyproject.toml`, `.golangci.yml`), `.editorconfig`. Standards in the repo beat your defaults.
4. Read each changed file in full, not only the hunk. Look at callers of any changed function signature (`git grep -n "funcName("`).
5. Run what the repo already runs, if you can:
   - Linters and type checkers from the repo config (`npm run lint`, `ruff check .`, `mypy`, `go vet ./...`, `golangci-lint run`).
   - Tests touching the changed code (`pytest -k`, `npm test -- <path>`, `go test ./pkg/...`).
   - `semgrep --config auto --baseline-commit origin/main` for new pattern hits only.
   - `gitleaks protect --staged -v` or `gitleaks detect --no-git -v` on the changed files.
6. Walk the checklist below. For each finding, record file, line, what goes wrong, and the fix.
7. Assign severity using the table in Output format. When unsure between two levels, pick the lower one and say why.
8. Drop findings a linter in CI will already catch, unless CI is not running that linter.
9. Write the review in the output format. Lead with blockers. Keep praise to one line if any.

## Checklist

Correctness

- Off-by-one in loops, slices, pagination (`range(len(x) - 1)`, `<=` vs `<`).
- Null, `None`, `undefined`, empty list and empty string handled at every new entry point.
- Errors are checked, not swallowed: no bare `except:`, no `catch (e) {}`, no ignored Go `err`.
- Async code awaits what it starts. No floating promises (`@typescript-eslint/no-floating-promises`).
- Shared state touched from goroutines, threads or workers is locked or immutable. Run `go test -race` for Go.
- Time zones: stored and compared in UTC. No naive `datetime.now()` for persisted values.
- Money and IDs are not floats.

Security (quick pass; send deep work to `security-audit`)

- User input reaches SQL only through parameters, never string formatting.
- No shell built from input (`subprocess(..., shell=True)`, `exec`, backticks).
- New endpoints check authorization, not only authentication.
- No secrets, tokens or keys in code, tests or fixtures. Fake values only (`AKIAEXAMPLEEXAMPLE00`).
- Logs do not print tokens, passwords, full card numbers or personal data.
- New dependencies are pinned and come from the expected registry.

Design and maintainability

- The change does one thing. Unrelated edits belong in a separate PR.
- New public functions and endpoints have names that match what they do.
- No copy of logic that already exists in the codebase (`git grep` for it).
- Config and feature flags read once at startup, not in hot paths.
- Dead code, commented-out blocks and leftover debug prints removed.

Tests

- New behavior has a test. A bug fix has a test that fails without the fix.
- Tests assert results, not only that code ran without throwing.
- No `sleep` based waits in tests, no real network calls.

Operability

- Errors carry enough context to debug (IDs, not payloads).
- Migrations are backward compatible with the currently deployed code.
- Breaking API changes are versioned or called out in the PR.

A longer per-language list lives in [references/language-checks.md](references/language-checks.md).

## Output format

Severity scale:

| Severity | Meaning | Merge? |
|---|---|---|
| blocker | Wrong result, data loss, security hole, broken build | No |
| major | Likely bug under real input, missing test for new logic, breaks a team standard | Fix before merge unless agreed |
| minor | Maintainability or clarity issue with a real cost | Author's call |
| nit | Style or naming preference | Optional |

Review template:

```markdown
## Summary
<one sentence on what the change does> <verdict: approve / request changes / comment>

## Findings
| # | Severity | File | Line | Issue | Fix |
|---|---|---|---|---|---|
| 1 | blocker | src/orders/api.py | 42 | Order ID from the URL goes into an f-string SQL query | Use a bound parameter: `cur.execute("... WHERE id = %s", (order_id,))` |
| 2 | major | src/orders/api.py | 58 | No test for the 404 path | Add `test_get_order_returns_404_for_unknown_id` |

## Checks run
- ruff check . : clean
- pytest tests/orders : 14 passed
- semgrep --baseline-commit origin/main : 1 new finding (row 1)

## Not reviewed
<files skipped and why, e.g. generated code, lockfiles>
```

If there are no findings, say so and list the checks you ran. Do not invent nits to fill the table.

## Examples

Bad review comment:

```text
This could be improved. Consider better error handling here.
```

Good review comment:

```text
major | src/billing/charge.ts:31
`await stripe.charges.create(...)` can throw on a card decline, and the
catch block only logs it. The caller then marks the invoice as paid.
Fix: rethrow a `PaymentDeclinedError` and let `markPaid` run only on success.
Test: add a case where the client mock rejects with `card_declined`.
```

Bad code that should get a blocker:

```python
def get_user(conn, user_id):
    return conn.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchone()
```

The fix to suggest:

```python
def get_user(conn, user_id: int):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
```

Bad severity call: marking a missing trailing comma as `major`. Good: `nit`, or leave it to the formatter.
