# Language checks for code review

Quick checks by language. Use the ones that match the diff. Tools named here are the usual ones; prefer whatever the repo already configures.

## Python

- `ruff check .` and `mypy` (or `pyright`) pass on changed files.
- Mutable default arguments (`def f(x=[])`). Ruff rule `B006`.
- Bare `except:` or `except Exception: pass`. Ruff rules `E722`, `S110`.
- `subprocess` with `shell=True` and any variable in the command. Bandit `B602`.
- `yaml.load` without `Loader=yaml.SafeLoader`. Bandit `B506`.
- `pickle.loads` on data from outside the process. Bandit `B301`.
- `requests` calls without `timeout=`. Ruff rule `S113`.
- Naive datetimes (`datetime.now()` instead of `datetime.now(timezone.utc)`). Ruff `DTZ005`.

## JavaScript and TypeScript

- `tsc --noEmit` passes. No new `any` or `// @ts-ignore` without a comment saying why.
- Floating promises. ESLint `@typescript-eslint/no-floating-promises`.
- `==` instead of `===`. ESLint `eqeqeq`.
- `dangerouslySetInnerHTML` or `innerHTML` with user data.
- `JSON.parse` on untrusted input without try/catch and schema validation (zod, ajv).
- Missing `key` props or keys built from array index in lists that reorder.
- `useEffect` without a dependency array, or with a missing dependency (`react-hooks/exhaustive-deps`).

## Go

- `go vet ./...` and `golangci-lint run` pass.
- Ignored errors (`_ = f()` or a call with no assignment). `errcheck` linter.
- Goroutines without a way to stop them (no `context.Context` or done channel).
- `defer` inside a loop holding file handles or locks.
- Data races. Run `go test -race ./...`.
- `http.Client{}` without `Timeout`.
- SQL built with `fmt.Sprintf`. `gosec` rule `G201`.

## Java and Kotlin

- `equals` without `hashCode`.
- Resources not closed (use try-with-resources or `.use {}`).
- `catch (Exception e) {}` with an empty body.
- String concatenation into JPQL or JDBC queries. Use `PreparedStatement` or named parameters.
- Jackson default typing enabled (`enableDefaultTyping`) on untrusted input.

## SQL and migrations

- New columns on large tables added as nullable or with a default that does not rewrite the table.
- Indexes created with `CONCURRENTLY` on Postgres.
- No `DROP COLUMN` in the same release that stops reading the column.
- Detailed migration checks belong to the `migration-helper` skill.

## Shell

- `shellcheck` passes.
- `set -eu` at the top of scripts that should fail fast.
- Variables quoted (`"$var"`), especially paths.
- No `curl ... | sh` from a URL without a pinned checksum.
