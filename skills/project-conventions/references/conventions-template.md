# CONVENTIONS.md template

Copy this into the target repo as `CONVENTIONS.md` and fill each section from evidence in the codebase. Delete sections that do not apply. Replace every `<placeholder>`.

```markdown
# Conventions

Last reviewed: <YYYY-MM-DD> by <team or handle>

## 1. Overview

<Two or three sentences: what the service or app does, who uses it, how it is deployed.>

## 2. Architecture and layout

Style: <layered / hexagonal / modular monolith / microservice>

| Path | Holds | Rule |
|---|---|---|
| `src/api/` | HTTP handlers | No business logic. Validate, call a service, map errors. |
| `src/services/` | Business logic | No framework imports. |
| `src/repositories/` | DB access | Only place that imports the ORM. |
| `tests/` | Tests | Mirrors `src/` layout. |

Dependencies point inward: api -> services -> repositories. Never the reverse.

## 3. Stack and approved libraries

| Need | Use | Do not add |
|---|---|---|
| Runtime | <Python 3.12 / Node 20.x / Go 1.23> | |
| Web framework | <FastAPI / Express / chi> | |
| HTTP client | <httpx / fetch / net/http> | <requests / axios> |
| Validation | <pydantic / zod> | hand-rolled validators |
| ORM / DB | <SQLAlchemy 2 / Prisma / sqlc> | |
| Logging | <structlog / pino / slog> | print, console.log |
| Tracing | OpenTelemetry SDK, OTLP exporter | vendor SDKs directly |
| Testing | <pytest / vitest / go test> | |

Adding a new dependency needs: a reason in the PR, a license check (MIT, Apache-2.0, BSD are fine), and a pinned version.

## 4. Code style

- Formatter: <ruff format / prettier / gofmt>. Runs in CI job `<name>`.
- Linter: <ruff / eslint / golangci-lint> with config in `<file>`.
- Naming: <rules>.
- File size: split modules past about <400> lines.

## 5. Error handling and logging

- Error base type: `<app.errors.DomainError>`. Map to HTTP in `<file>`.
- Wrap errors with context (`fmt.Errorf("load order %s: %w", id, err)`).
- Log format: JSON, fields `timestamp`, `level`, `msg`, `request_id`, `trace_id`.
- Never log: passwords, tokens, API keys, session IDs, full card numbers, government IDs, request bodies from `<sensitive routes>`.

## 6. Configuration and secrets

- Config from env vars, parsed once in `<settings module>`.
- Secrets from `<Vault / AWS Secrets Manager / GCP Secret Manager / SOPS>`. Never in `.env` files committed to git.
- Local dev uses `.env.example` with fake values (`API_KEY=changeme`).

## 7. Testing

- Unit tests: `<command>`. Integration tests: `<command>` (needs Docker).
- Integration tests marked with `<@pytest.mark.integration / build tag>`.
- Coverage gate: <N> percent on changed lines (CI job `<name>`).
- No real network or clock in unit tests.

## 8. Security defaults

| Check | Tool | Blocks merge on |
|---|---|---|
| SAST | Semgrep (`<config>`) | ERROR severity |
| Secrets | gitleaks | any finding |
| Dependencies | <Trivy / Dependabot / Renovate> | critical and high with a fix |
| IaC | <Checkov / tfsec> | <policy> |
| Containers | Trivy image scan | critical |

- Authn: <how>. Authz: checked in <layer>, deny by default.
- All external input validated at the API layer with <validation lib>.

## 9. Git and review

- Commits: Conventional Commits (`type(scope): summary`).
- Branches: `<feat/short-name>`. Merge: <squash / rebase>.
- Reviews: <N> approvals, CODEOWNERS for `<paths>`.
- PR template: `.github/pull_request_template.md`.

## 10. Anti-patterns

Format: Do not X. Do Y instead, because Z.

- Do not call the DB from handlers. Call a service, because handlers get reused by the CLI.
- Do not catch and ignore errors. Wrap and return them, because silent failures hid <past issue>.
- Do not add a new HTTP client. Use <client>, because it carries tracing and retries.
- <add more from review history and postmortems>
```
