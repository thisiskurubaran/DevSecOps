---
name: docs-writer
description: Write and update developer documentation (READMEs, docstrings and code comments, ADRs, CHANGELOG entries in Keep a Changelog format, and API usage docs) based on the actual code, with commands and examples that run. Use when the user asks to document a project, module, function or decision, write or fix a README, add docstrings or JSDoc, record an architecture decision, or update the changelog.
---

# Docs Writer

## When to use

- "Write a README for this repo", "our README is out of date".
- "Add docstrings to this module", "document these exported functions".
- "Write an ADR for moving from REST to gRPC".
- "Add a changelog entry for this change", "set up a CHANGELOG".

Not for: commit messages and PR descriptions (use `commit-pr-writer`), recording team coding rules and anti-patterns (use `project-conventions`), OpenAPI specs for a new endpoint (use `api-scaffolder`), or incident write-ups (use `incident-postmortem`).

## Steps

1. Read before writing. Open the entry points, `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml`, the `Makefile` or `justfile`, CI config, `.env.example` and existing docs. Docs must describe what the code does now, not what the old README claimed.
2. Identify the reader: a new contributor, an API consumer, an operator, or a future maintainer reading an ADR. Write for that one reader.
3. Pick the doc type and use its template from [references/templates.md](references/templates.md).
4. Run every command you put in the docs, or mark it clearly as untested. Copy exact script names (`npm run dev`, `make test`, `uv run pytest`). Do not invent flags.
5. Use real, minimal examples. Show the input and the output. Use `example.com`, `user@example.com` and placeholders like `<your-api-key>` for anything sensitive.
6. For docstrings, follow the format the project already uses (Google, NumPy or reST for Python, JSDoc / TSDoc, Javadoc, Go doc comments starting with the identifier name). Document behavior callers cannot see from the signature: units, errors raised, side effects, thread safety, nullability.
7. For ADRs, record context, the decision, options considered and consequences, including the bad ones. One decision per ADR. Number them (`docs/adr/0007-use-postgres-for-queues.md`). Never edit an accepted ADR's decision; supersede it with a new one.
8. For changelogs, add entries under `## [Unreleased]` using Keep a Changelog groups: Added, Changed, Deprecated, Removed, Fixed, Security. Write for users of the software, not for the team. Link issues or PRs.
9. Run doc linters if present (`markdownlint`, `vale`, `lychee` for links, `pydocstyle` / `ruff` rule `D`, `eslint-plugin-jsdoc`, `doctest`).
10. Report what you changed and anything you could not verify.

## Checklist

README
- [ ] First paragraph says what the project does and who it is for, in plain words.
- [ ] Install and run steps work from a clean clone. Prerequisites list versions (`Node 20+`, `Python 3.12`, `Docker 24+`).
- [ ] Config documented: every env var from `.env.example` with purpose and default. No real values.
- [ ] One usage example with real output.
- [ ] Links to CONTRIBUTING, LICENSE and SECURITY policy if they exist.
- [ ] Badges only if they are live and useful (CI status, coverage). No vanity badges.

Docstrings and comments
- [ ] Every public function, class and module has a docstring. Private helpers only when the logic is not obvious.
- [ ] Parameters, return value, raised errors and side effects stated.
- [ ] Comments explain why, not what. Delete comments that restate the code.
- [ ] `TODO` comments have an owner or issue link (`TODO(#123): ...`).
- [ ] Examples in docstrings run as tests where the language supports it (`python -m doctest`, Rust doc tests, Go `Example` functions).

ADR
- [ ] Status set: Proposed, Accepted, Deprecated or Superseded by ADR-NNNN.
- [ ] At least two options considered, with reasons for rejecting the others.
- [ ] Consequences include costs and risks, including security and operational impact.
- [ ] Dated, with deciders listed by role or handle.

Changelog
- [ ] Keep a Changelog format with `[Unreleased]` at the top and compare links at the bottom.
- [ ] Entries grouped (Added, Changed, Deprecated, Removed, Fixed, Security).
- [ ] Breaking changes called out and placed first in Changed or Removed, with migration steps.
- [ ] Security fixes reference the CVE or advisory ID if public.

Safety
- [ ] No secrets, tokens, internal hostnames, customer names or real emails in examples. Run `gitleaks detect --no-git -v` on the docs folder.
- [ ] Screenshots and logs scrubbed of IPs, account IDs and session cookies.

## Output format

For new or rewritten docs, write the file directly, then reply:

```markdown
### Docs updated

| File | Change |
|---|---|
| README.md | rewrote Install and Configuration, added Usage example |
| src/billing/tax.py | Google-style docstrings on 4 public functions |
| docs/adr/0007-use-postgres-for-queues.md | new ADR, status Proposed |
| CHANGELOG.md | 2 entries under [Unreleased] |

### Verified
- `make setup && make test` ran from a clean clone.
- `lychee README.md` found no broken links.

### Not verified
- Windows install steps (no Windows machine available).
```

For a docs review of existing files, use a findings table: severity, file, line, issue, fix.

## Examples

Bad README opening: vague, no commands.

```markdown
# Orbit
Orbit is a powerful, flexible platform that helps teams do more with their data.
## Getting started
Install the dependencies and run the app.
```

Good README opening: says what it is, how to run it.

````markdown
# Orbit
Orbit syncs Stripe invoices into Postgres every 5 minutes so finance can query them with SQL.

## Quick start
Requires Python 3.12 and Docker.

```sh
cp .env.example .env          # set STRIPE_API_KEY=<your-test-key>
docker compose up -d db
uv sync && uv run orbit sync --since 2024-01-01
```
````

Bad docstring: restates the signature.

```python
def retry(fn, attempts=3, delay=1.0):
    """Retries a function."""
```

Good docstring: covers units, behavior and errors.

```python
def retry(fn, attempts=3, delay=1.0):
    """Call fn until it succeeds or attempts run out.

    Waits delay seconds before the first retry and doubles the wait
    after each failure. Only retries on ConnectionError and TimeoutError.

    Args:
        fn: Zero-argument callable.
        attempts: Total calls including the first. Must be >= 1.
        delay: Initial wait in seconds.

    Returns:
        Whatever fn returns.

    Raises:
        The last exception from fn if every attempt fails.
    """
```

Bad changelog entry: internal jargon, no group.

```markdown
- refactored svc layer, fixed the thing from standup
```

Good changelog entry:

```markdown
## [Unreleased]
### Fixed
- Invoices with a zero total no longer fail to sync (#412).
### Security
- Upgrade `jsonwebtoken` to 9.0.2 to fix CVE-2022-23529.
```
