<div align="center">

# DevSecOps Skills

Security and delivery workflows for Claude, packaged as installable skills.

[![Release](https://img.shields.io/github/v/release/thisiskurubaran/DevSecOps-Skills?sort=semver)](https://github.com/thisiskurubaran/DevSecOps-Skills/releases)
[![License: MIT](https://img.shields.io/github/license/thisiskurubaran/DevSecOps-Skills)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-36-2ea44f)](#skills)
[![Claude Code support](https://img.shields.io/badge/Claude_Code-supported-D97757)](#claude-code)
[![claude.ai](https://img.shields.io/badge/claude.ai-supported-D97757)](#claudeai-and-claude-desktop)
[![Conventional Commits](https://img.shields.io/badge/Conventional_Commits-1.0.0-FE5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![Last commit](https://img.shields.io/github/last-commit/thisiskurubaran/DevSecOps-Skills)](https://github.com/thisiskurubaran/DevSecOps-Skills/commits/main)

[Quick start](#quick-start) ·
[Skills](#skills) ·
[Install](#install) ·
[Usage](#usage) ·
[Contributing](#contributing)

</div>

---

Each skill is a folder with a `SKILL.md` that teaches Claude one workflow: review a Terraform module, audit a GitHub Actions workflow, triage Trivy output, write a blameless postmortem. Claude loads a skill when your request matches its description, then follows its steps, checklist and output format.

- 36 skills across the delivery lifecycle, from planning to incident response
- Findings come back in a consistent table: severity, file, line and a concrete fix
- Checks are built around real tools: Semgrep, Trivy, Checkov, zizmor, cosign, Falco, Prowler, OPA, Kyverno
- Install one folder or all of them
- Plain Markdown, so you can read, fork and adapt it to your team's standards

## Quick start

```bash
git clone https://github.com/thisiskurubaran/DevSecOps-Skills.git
mkdir -p ~/.claude/skills
cp -r DevSecOps-Skills/skills/iac-review ~/.claude/skills/
```

Start a new Claude Code session and ask:

```
Review the Terraform in infra/ before I merge.
```

## Skills

### Plan

| Skill | What it does |
|---|---|
| [threat-modeling](skills/threat-modeling) | Runs STRIDE on new features and maps trust boundaries |
| [privacy-review](skills/privacy-review) | Maps personal data flows and checks retention, consent and deletion against GDPR and CCPA |

### Develop

| Skill | What it does |
|---|---|
| [code-review](skills/code-review) | Checks diffs against team standards and ranks findings by severity |
| [commit-pr-writer](skills/commit-pr-writer) | Writes commit messages and PR descriptions in a set format |
| [test-generator](skills/test-generator) | Writes unit and integration tests with edge cases |
| [debugging-playbook](skills/debugging-playbook) | Reproduces and isolates the bug, fixes it, then adds a regression test |
| [project-conventions](skills/project-conventions) | Template for recording architecture, libraries and anti-patterns |
| [api-scaffolder](skills/api-scaffolder) | Creates a route, validation, tests and docs in the project's structure |
| [migration-helper](skills/migration-helper) | Writes safe migrations with rollback steps and locking checks |
| [refactoring-guide](skills/refactoring-guide) | Makes small, behavior-preserving changes and keeps tests green |
| [performance-review](skills/performance-review) | Finds N+1 queries, missing indexes, re-renders and memory leaks |
| [docs-writer](skills/docs-writer) | Writes READMEs, docstrings, ADRs and changelogs |

### Secure

| Skill | What it does |
|---|---|
| [security-audit](skills/security-audit) | Checks code for OWASP Top 10 issues, injection and auth gaps |
| [auth-review](skills/auth-review) | Reviews OAuth/OIDC flows, JWT validation, sessions, MFA and RBAC/ABAC logic |
| [api-security-review](skills/api-security-review) | Checks OpenAPI specs, GraphQL schemas and endpoints against the OWASP API Top 10 |
| [llm-app-security](skills/llm-app-security) | Reviews LLM apps, RAG and agents against the OWASP Top 10 for LLM Applications |
| [sast-dast-triage](skills/sast-dast-triage) | Sorts scanner output into real findings and false positives, then ranks them |
| [dast-setup](skills/dast-setup) | Wires ZAP or Nuclei scans into CI against preview environments, with auth and baselines |
| [dependency-supply-chain](skills/dependency-supply-chain) | Reviews SCA results, CVEs, licenses and SBOMs |
| [secrets-management](skills/secrets-management) | Finds hardcoded secrets, plans rotation, enforces Vault or KMS |

### Build

| Skill | What it does |
|---|---|
| [cicd-pipeline-builder](skills/cicd-pipeline-builder) | Writes GitHub Actions or GitLab CI with security gates |
| [pipeline-hardening](skills/pipeline-hardening) | Audits existing GitHub Actions and GitLab CI for unpinned actions, injection, broad tokens and long-lived keys |
| [container-security](skills/container-security) | Hardens Dockerfiles and reviews image scan results |
| [artifact-signing](skills/artifact-signing) | Signs images and release files with cosign, adds SLSA provenance and verifies at deploy time |

### Infra

| Skill | What it does |
|---|---|
| [iac-review](skills/iac-review) | Checks Terraform and CloudFormation for misconfigurations |
| [k8s-manifest-review](skills/k8s-manifest-review) | Checks pod security, RBAC, network policies and resource limits |
| [helm-review](skills/helm-review) | Checks Helm values defaults, templates, dependencies and chart provenance |
| [cloud-iam-review](skills/cloud-iam-review) | Finds over-privileged roles and enforces least privilege |
| [cspm-triage](skills/cspm-triage) | Turns Prowler, ScoutSuite or Security Hub findings into a ranked fix plan |

### Compliance

| Skill | What it does |
|---|---|
| [policy-as-code](skills/policy-as-code) | Writes OPA/Rego or Kyverno rules, maps controls to SOC 2, ISO 27001, PCI |
| [risk-acceptance](skills/risk-acceptance) | Writes risk acceptance records with owner, expiry and compensating controls |

### Deploy

| Skill | What it does |
|---|---|
| [release-checklist](skills/release-checklist) | Covers versioning, CI checks, feature flags and rollback plans |

### Operate

| Skill | What it does |
|---|---|
| [observability-setup](skills/observability-setup) | Sets up logs, metrics, traces, alerts and SLOs without leaking PII |
| [runtime-security](skills/runtime-security) | Writes and tunes Falco and Tetragon rules and triages runtime alerts |
| [vuln-management](skills/vuln-management) | Sets fix SLAs, prioritizes with EPSS and KEV, dedupes across scanners and reports aging |
| [incident-response](skills/incident-response) | Guides triage, containment, comms and escalation |
| [incident-postmortem](skills/incident-postmortem) | Writes a blameless timeline, root cause and action items |

## Install

Clone the repo once, then pick your platform.

```bash
git clone https://github.com/thisiskurubaran/DevSecOps-Skills.git
```

### Claude Code

Claude Code reads skills from a directory. No zip needed.

```bash
# One skill, available in all your projects
mkdir -p ~/.claude/skills
cp -r DevSecOps-Skills/skills/iac-review ~/.claude/skills/

# Every skill
cp -r DevSecOps-Skills/skills/* ~/.claude/skills/

# Project scope, shared with your team through your repo
mkdir -p .claude/skills
cp -r DevSecOps-Skills/skills/iac-review .claude/skills/
```

Start a new session after copying. Claude picks a skill when your request matches its description. You can also call one directly, for example `/iac-review`.

### claude.ai and Claude Desktop

Zip the skill folder so the folder itself is the top level of the zip:

```bash
cd DevSecOps-Skills/skills

# One skill
zip -r iac-review.zip iac-review/

# Every skill, one zip each
for d in */; do zip -qr "${d%/}.zip" "$d"; done
```

Then:

1. Go to **Customize > Skills**.
2. Click **+**, then **Create skill**.
3. Choose **Upload a skill** and select the zip.

The zip must contain `iac-review/SKILL.md`, not a bare `SKILL.md`. Skills need code execution turned on. On individual plans that is under **Settings > Capabilities**. On Team and Enterprise plans an owner may need to enable skills for the organization.

### Updating

```bash
cd DevSecOps-Skills && git pull
cp -r skills/* ~/.claude/skills/
```

For claude.ai, re-zip and upload the skills that changed. Check the [changelog](CHANGELOG.md) or [releases](https://github.com/thisiskurubaran/DevSecOps-Skills/releases) to see what changed.

Docs: [Claude Code skills](https://code.claude.com/docs/en/skills) and [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## Usage

Ask for the work in plain language. Claude matches your request to a skill.

| You ask | Skill | You get |
|---|---|---|
| "Review this Terraform module before I open the PR." | `iac-review` | Findings table with severity, file, line and fixed HCL |
| "Can a fork PR exploit any of our workflows?" | `pipeline-hardening` | Risky triggers and injection points, with pinned and fixed YAML |
| "Here is the Trivy output for our API image. What actually needs fixing?" | `container-security`, `sast-dast-triage` | Real findings separated from noise, ranked by exposure |
| "Is our JWT validation safe?" | `auth-review` | Missing claim checks, algorithm issues and code fixes |
| "We are adding SSO login next sprint. Threat model it." | `threat-modeling` | Trust boundaries and STRIDE threats with mitigations |
| "Prod API is returning 500s and error rate is climbing." | `incident-response` | Triage steps, containment options and a status update draft |

Each skill has an `examples/test-prompts.md` with prompts that should and should not trigger it.

## How a skill is built

```
skills/<skill-name>/
├── SKILL.md        frontmatter (name, description) plus the instructions
├── references/     longer checklists and specs, loaded when needed
├── scripts/        helper scripts the skill can run (POSIX sh or Python stdlib)
└── examples/       test prompts and good vs bad samples
```

Every `SKILL.md` follows the same layout: **When to use**, **Steps**, **Checklist**, **Output format** and **Examples**. The `description` in the frontmatter decides when Claude picks the skill, so it names the files, tools and phrases that should trigger it.

## Contributing

Fixes, new checks and new skills are welcome.

- Found wrong or outdated advice? [Open a bug report](https://github.com/thisiskurubaran/DevSecOps-Skills/issues/new?template=bug_report.md).
- Want a new skill? [Open a skill request](https://github.com/thisiskurubaran/DevSecOps-Skills/issues/new?template=skill_request.md) first so we can agree on scope.
- Ready to write one? Read [CONTRIBUTING.md](CONTRIBUTING.md) for the skill format, style rules, testing steps and commit format.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Found a security problem in a skill or script, or a leaked secret in an example? Report it privately as described in [SECURITY.md](SECURITY.md). Please do not open a public issue.

## License

[MIT](LICENSE)
