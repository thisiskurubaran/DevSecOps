# Contributing

Thanks for helping out. This repo is a set of DevSecOps skills for Claude.
Each skill is a folder with a `SKILL.md` that teaches Claude one workflow.
Good contributions are small, specific, and tested.

## Ways to help

- Fix wrong or outdated advice in a skill
- Sharpen a skill's `description` so it triggers more reliably
- Add a missing check, tool, or example
- Propose a new skill (open a [skill request](.github/ISSUE_TEMPLATE/skill_request.md) first so we can agree on scope)

## Proposing a new skill

1. Open a skill request issue with the name, two trigger prompts, one
   non-trigger prompt, and how it differs from existing skills.
2. Wait for a thumbs up on scope before writing a lot of content.
3. Open a PR that adds the skill folder, a README table row, and a
   `CHANGELOG.md` entry under `[Unreleased]`.

## Skill format

```
skills/
  <skill-name>/
    SKILL.md
    references/   optional: long checklists, specs
    scripts/      optional: helper scripts the skill runs
    examples/     optional: good and bad samples, test prompts
```

`SKILL.md` starts with YAML frontmatter:

```markdown
---
name: iac-review
description: Review Terraform and CloudFormation for security misconfigurations. Use when the user shares IaC files, asks for an infra review, or opens a PR touching *.tf or CloudFormation templates.
---

# IaC Review

## When to use
## Steps
## Checklist
## Output format
## Examples
```

Rules:

- `name` is lowercase kebab-case and matches the folder name exactly.
  claude.ai rejects uploads where they differ.
- `description` says what the skill does and when to use it. Claude picks
  skills based on this text, so name the file types, tools, and phrases
  that should trigger it.
- Only use the frontmatter keys `name`, `description`, `license`,
  `compatibility`, `metadata`, and `allowed-tools`. claude.ai rejects
  uploads with other keys.
- Keep `SKILL.md` under 500 lines. Move long lists to `references/` and
  link to them.
- Put repeatable steps in `scripts/`. Use POSIX sh or Python 3 with the
  standard library only, and add a usage comment at the top.
- Define a clear output format, for example a findings table with
  severity, file, line, issue, and fix.
- Include at least one short bad vs good example.

## Testing a skill

1. Copy the folder to `~/.claude/skills/` and start a fresh Claude Code
   session.
2. Try two prompts that should trigger it and one that should not.
3. If it does not trigger, make the `description` more specific. If it
   triggers on the wrong prompt, narrow it.
4. Write the prompts in `examples/test-prompts.md` so others can repeat
   the test.

## Style rules

These apply to every file in the repo.

- No em dashes (—) or en dashes (–). Use a comma, colon, period,
  parentheses, or a plain hyphen.
- Write like a developer explaining something to a colleague. Short
  sentences, concrete examples.
- Skip filler openers, sales language, and dramatic one-line closers.
- Avoid stock words such as delve, leverage, robust, seamless, elevate,
  unlock, empower, game-changer, and cutting-edge.
- No emoji in headings. Do not bold the start of every bullet.
- No real secrets, tokens, internal hostnames, or customer data. Use
  `example.com` and obviously fake values.

Quick self check before you push:

```bash
# Dashes
grep -rnP '\x{2014}|\x{2013}' --exclude-dir=.git --exclude=CONTRIBUTING.md .

# Stock words
grep -rniwE "delve|leverage|seamless|robust|elevate|unlock|empower|tapestry|game-changer|cutting-edge" --exclude-dir=.git --exclude=CONTRIBUTING.md .

# Folder name matches frontmatter name
for d in skills/*/; do
  n=$(basename "$d")
  grep -q "^name: $n$" "$d/SKILL.md" || echo "name mismatch in $d"
done

# Secrets, if you have gitleaks installed
gitleaks detect --no-git -v
```

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/).

- Format: `type(scope): short summary`
- Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `ci`, `test`
- Scope is the skill folder or area, for example `iac-review` or `readme`
- Imperative mood, lowercase, no trailing period, under 72 characters
- Add a body when the reason is not obvious, wrapped at 72 characters
- One logical change per commit

```
feat(container-security): add dockerfile hardening checklist

Covers non-root users, pinned base image digests, and multi-stage
builds. Image scan triage lives in the sast-dast-triage skill.
```

## Versioning

The repo uses semantic versioning as a whole:

- New skill: minor bump
- Fix or wording change: patch bump
- Renaming or removing a skill: major bump, since it breaks installs

Add your change to `CHANGELOG.md` under `[Unreleased]` in the same PR.

## PR checklist

- [ ] Frontmatter is valid and `name` matches the folder
- [ ] Description says what it does and when to use it
- [ ] Steps, checklist, output format, and a bad vs good example
- [ ] Tested with trigger and non-trigger prompts, noted in `examples/`
- [ ] README table and `CHANGELOG.md` updated
- [ ] No em dashes, no secrets, style checks pass

By contributing you agree that your work is released under the
[MIT License](LICENSE) and that you follow the
[Code of Conduct](CODE_OF_CONDUCT.md).
