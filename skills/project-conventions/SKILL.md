---
name: project-conventions
description: Create or update a CONVENTIONS.md that records a project's architecture, layout, approved libraries, coding rules, security defaults and anti-patterns, based on what the codebase actually does. Use when the user asks to document team conventions, onboard a new repo, write down "how we do things here", or set rules that other skills and reviewers should follow.
---

# Project Conventions

Write down how this project works so people and tools stop guessing. Base every rule on evidence in the repo: config files, existing code, CI. A conventions file that disagrees with the code is worse than none.

## When to use

- "Document our conventions", "write a CONVENTIONS.md", "what are the house rules here?"
- Onboarding to an unfamiliar repo and the user wants the patterns captured.
- After an incident or review round, to record a new rule or anti-pattern.
- Before running `code-review`, so the review has a standard to check against.

Not for: README or API docs (use `docs-writer`), architecture decision records for one decision (use `docs-writer`, ADR format), or reviewing a diff against the conventions (use `code-review`).

## Steps

1. Check for existing docs first: `CONVENTIONS.md`, `docs/conventions.md`, `CONTRIBUTING.md`, `docs/adr/`, `ARCHITECTURE.md`. Update rather than duplicate.
2. Map the stack from config files:
   - Languages and versions: `.tool-versions`, `.nvmrc`, `.python-version`, `go.mod`, `pyproject.toml`, `package.json` `engines`.
   - Frameworks and libraries: dependency manifests and lockfiles.
   - Lint and format: `.eslintrc*`, `prettier` config, `ruff.toml`, `.golangci.yml`, `.editorconfig`.
   - CI gates: `.github/workflows/*.yml`, `.gitlab-ci.yml`. Note which checks block merges.
   - Security tooling: `.semgrep.yml`, `.gitleaks.toml`, `.trivyignore`, `.checkov.yml`, `renovate.json`, `dependabot.yml`, `CODEOWNERS`.
3. Map the layout: `tree -L 2 -d` (or `find . -maxdepth 2 -type d -not -path './.git*'`). Name what each top-level folder holds.
4. Sample the code for patterns. Read 3 to 5 representative files per layer (handler, service, repository, test). Record what they do the same way: error handling, logging, config loading, dependency injection, naming.
5. Find disagreements. Where two patterns exist (for example `axios` and `fetch`), check `git log --format='%ad %s' --date=short -- <file>` to see which is newer, and ask the user which one is the rule.
6. Fill the template in [references/conventions-template.md](references/conventions-template.md). Keep each rule to one line plus a short example when the rule is not obvious.
7. Write anti-patterns as "Do not X. Do Y instead, because Z." Pull them from review comments, postmortems and lint suppressions (`git grep -n "eslint-disable\|noqa\|nolint"`).
8. Mark anything you inferred but could not confirm with `(unconfirmed)` and list it for the user to check.
9. Point tools at the file. Suggest linking it from `CONTRIBUTING.md` and the PR template so reviewers use it.
10. Keep it short. If a section passes about 40 lines, move details to `docs/` and link.
11. Keep it current. Add a `Last reviewed: <date>` line at the top, and suggest a CODEOWNERS entry so changes to the file get a reviewer:

    ```text
    /CONVENTIONS.md  @example-org/platform-team
    ```

12. Where a rule can be enforced by a tool, say which one and prefer the tool over prose. Examples: an ESLint `no-restricted-imports` rule to ban a library, a Semgrep custom rule for a banned call, a `.golangci.yml` `depguard` list for blocked packages.

## Checklist

- Every rule traces to a config file, CI job or repeated code pattern, or is marked `(unconfirmed)`.
- Versions are exact where the repo pins them (Node 20.x, Python 3.12, Go 1.23).
- Approved libraries list says what each is for, and what not to add instead (for example "HTTP client: httpx. Do not add requests.").
- Error handling rule names the actual error types or helpers in the codebase.
- Logging rule names the logger, the format (JSON or text), and what must never be logged (tokens, passwords, full card numbers, personal data).
- Config rule says where config comes from (env vars, a settings module) and where secrets come from (Vault, AWS Secrets Manager, SOPS), never from committed files.
- Testing rule names the framework, the folder, how to run unit vs integration tests, and the coverage gate if CI has one.
- Security defaults list the scanners CI runs (Semgrep, gitleaks, Trivy, Checkov) and which findings block a merge.
- Git rules match the repo: commit format, branch naming, merge strategy, required reviews.
- Anti-patterns each come with the preferred alternative.
- No internal hostnames, real account IDs or customer names. Use `example.com` and placeholders.

## Output format

A `CONVENTIONS.md` at the repo root (or `docs/conventions.md` if the repo keeps docs there), using the sections in [references/conventions-template.md](references/conventions-template.md):

1. Overview
2. Architecture and layout
3. Stack and approved libraries
4. Code style
5. Error handling and logging
6. Configuration and secrets
7. Testing
8. Security defaults
9. Git and review
10. Anti-patterns

Then a short list for the user:

```markdown
Unconfirmed items to check:
- <rule> (seen in <file>, but <conflicting file> does it differently)
```

## Examples

Bad (generic, no evidence, nothing to check against):

```markdown
## Code style
- Write clean, readable code.
- Follow best practices for error handling.
- Use good names.
```

Good (specific, tied to the repo):

```markdown
## Code style
- Python 3.12. Formatting by `ruff format`, lint by `ruff check` (CI job `lint`).
- Type hints on all public functions. `mypy --strict` runs on `src/` only.
- Module names are nouns (`invoices.py`), functions are verbs (`create_invoice`).

## Error handling and logging
- Raise subclasses of `app.errors.DomainError`. The API layer maps them to
  HTTP codes in `app/api/errors.py`. Do not raise `HTTPException` from services.
- Log with `structlog.get_logger()`, JSON output. Include `request_id`.
  Never log request bodies from `/auth/*`.
```

Bad anti-pattern entry:

```markdown
- Don't use raw SQL.
```

Good:

```markdown
- Do not build SQL with f-strings. Use SQLAlchemy Core with bound params
  (`select(User).where(User.id == user_id)`), because two past bugs were
  injection via report filters. Semgrep rule `python.sqlalchemy.security`
  blocks this in CI.
```
