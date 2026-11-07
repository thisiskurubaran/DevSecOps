---
name: commit-pr-writer
description: Write commit messages in Conventional Commits format and pull request descriptions from a fixed template, based on the actual staged diff. Use when the user asks for a commit message, wants to split changes into commits, or needs a PR title and description written or cleaned up.
---

# Commit and PR Writer

Turn a diff into a commit message and a PR description that a reviewer can act on. Describe what changed and why, in the project's format, and nothing the diff does not show.

## When to use

- "Write a commit message for this", "what should I call this commit?"
- The user has a pile of unstaged changes and wants them split into logical commits.
- "Write the PR description", "fill in the PR template", "clean up this PR body".

Not for: release notes and changelog entries (use `docs-writer` or `release-checklist`), reviewing the code itself (use `code-review`).

## Steps

1. Read the real change, not the user's summary of it:
   - Commit: `git diff --staged` and `git diff --staged --stat`.
   - PR: `git log --oneline origin/main..HEAD` and `git diff --stat origin/main...HEAD`.
2. Check the project's format before using the default:
   - `commitlint.config.*`, `.commitlintrc*`, or a `commit-msg` hook in `.husky/` or `.git/hooks/`.
   - `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/`.
   - `git log --oneline -20` to copy the scope names and tone the team already uses.
3. Decide if this is one commit or several. Split when the diff mixes:
   - A refactor and a behavior change.
   - Two unrelated features or fixes.
   - Formatting churn and real edits.
   Suggest `git add -p` or explicit paths per commit. Never suggest `git add .` for a split.
4. Pick the type and scope (see Checklist). Scope is the module, package or folder, lowercase.
5. Write the summary line: imperative mood, lowercase after the colon, no trailing period, under 72 characters total.
6. Write a body when the reason is not obvious from the summary. Explain why, the old behavior, and any risk. Wrap at 72 characters.
7. Add footers only when they apply: `BREAKING CHANGE: ...`, `Refs: #123`, `Closes #123`.
8. For a PR, fill the template below (or the repo's template). Pull testing steps from the test files in the diff.
9. Validate the message. Run `scripts/check-commit-msg.sh <file>` or `npx commitlint --edit <file>` if the repo has commitlint.
10. Show the message to the user. Do not run `git commit` or `gh pr create` unless they ask.

## Checklist

Types (Conventional Commits 1.0.0):

| Type | Use for |
|---|---|
| feat | New user-facing behavior |
| fix | Bug fix |
| docs | Docs only |
| refactor | Code change with no behavior change |
| perf | Faster or lighter, same behavior |
| test | Tests only |
| build | Build system, dependencies, Dockerfile |
| ci | Pipeline config (`.github/workflows/`, `.gitlab-ci.yml`) |
| chore | Tooling and housekeeping that fits nothing else |
| revert | Reverting an earlier commit |

Summary line:

- Matches `^(feat|fix|docs|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?!?: .+`.
- 72 characters or fewer.
- Imperative: "add", "fix", "remove", not "added" or "adds".
- Says what changed, not "update files" or "misc fixes".
- `!` after the scope, or a `BREAKING CHANGE:` footer, for any breaking API, config or schema change.

Body:

- Blank line between summary and body.
- Explains why. The diff already shows what.
- Mentions any security impact plainly (for example "stops logging the session token").
- No secrets, internal hostnames, customer names or ticket text with personal data.

PR description:

- Title follows the same format as a commit summary (squash merges reuse it).
- Links the issue with `Closes #N` so GitHub closes it on merge.
- Testing section lists commands a reviewer can run.
- Calls out migrations, new env vars, feature flags and rollback steps.
- Screenshots or sample output for UI or CLI changes.
- No attribution trailers or tool signatures unless the project's template asks for them.

## Output format

Commit message:

```text
<type>(<scope>): <summary under 72 chars>

<why this change, wrapped at 72 chars>

<footers: BREAKING CHANGE, Refs, Closes>
```

PR description:

```markdown
## What
<two or three sentences on the change>

## Why
<problem it solves, link to issue>

Closes #<n>

## How
- <key implementation point>
- <key implementation point>

## Testing
- [ ] `<command a reviewer can run>`
- [ ] <manual step and expected result>

## Risk and rollback
<what could break, how to roll back, flags or migrations involved>

## Checklist
- [ ] Tests added or updated
- [ ] Docs updated
- [ ] No secrets or personal data in code, logs or fixtures
```

When splitting, output a numbered list: files for each commit, then each message.

## Examples

Bad commit:

```text
Updated stuff and fixed bug
```

Good commit:

```text
fix(auth): reject expired refresh tokens

The refresh endpoint checked the signature but not the exp claim, so
a stolen refresh token stayed valid forever. Validate exp and return
401 with error=invalid_grant.

Closes #412
```

Bad split (one commit for everything):

```text
feat: new export, rename helpers, bump eslint
```

Good split:

```text
1. refactor(utils): rename date helpers to match module names
   files: src/utils/date.ts, src/utils/date.test.ts
2. feat(reports): add csv export for monthly report
   files: src/reports/export.ts, src/reports/export.test.ts
3. build(deps): bump eslint to 9.12.0
   files: package.json, package-lock.json
```

Bad breaking change (no marker):

```text
feat(api): change /users response to paginated object
```

Good:

```text
feat(api)!: return paginated object from /users

BREAKING CHANGE: GET /users now returns {"items": [...], "next": "..."}
instead of a bare array. Clients must read .items.
```
