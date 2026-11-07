# DevSecOps Skills

A collection of DevSecOps skills for [Claude](https://claude.ai). Each skill
is a folder with a `SKILL.md` that teaches Claude one workflow: reviewing a
diff, checking Terraform, writing a CI pipeline with security gates, running
an incident postmortem, and so on.

Install only the skills you want. They work in Claude Code, claude.ai, and
Claude Desktop.

## Skills

| Skill | Stage | What it does |
|---|---|---|
| [code-review](skills/code-review) | Develop | Checks diffs against team standards and ranks findings by severity |
| [commit-pr-writer](skills/commit-pr-writer) | Develop | Writes commit messages and PR descriptions in a set format |
| [test-generator](skills/test-generator) | Develop | Writes unit and integration tests with edge cases |
| [debugging-playbook](skills/debugging-playbook) | Develop | Reproduces and isolates the bug, fixes it, then adds a regression test |
| [project-conventions](skills/project-conventions) | Develop | Template for recording architecture, libraries and anti-patterns |
| [api-scaffolder](skills/api-scaffolder) | Develop | Creates a route, validation, tests and docs in the project's structure |
| [migration-helper](skills/migration-helper) | Develop | Writes safe migrations with rollback steps and locking checks |
| [refactoring-guide](skills/refactoring-guide) | Develop | Makes small, behavior-preserving changes and keeps tests green |
| [performance-review](skills/performance-review) | Develop | Finds N+1 queries, missing indexes, re-renders and memory leaks |
| [docs-writer](skills/docs-writer) | Develop | Writes READMEs, docstrings, ADRs and changelogs |
| [threat-modeling](skills/threat-modeling) | Plan | Runs STRIDE on new features and maps trust boundaries |
| [security-audit](skills/security-audit) | Secure | Checks code for OWASP Top 10 issues, injection and auth gaps |
| [sast-dast-triage](skills/sast-dast-triage) | Secure | Sorts scanner output into real findings and false positives, then ranks them |
| [dependency-supply-chain](skills/dependency-supply-chain) | Secure | Reviews SCA results, CVEs, licenses and SBOMs |
| [secrets-management](skills/secrets-management) | Secure | Finds hardcoded secrets, plans rotation, enforces Vault or KMS |
| [api-security-review](skills/api-security-review) | Secure | Checks OpenAPI specs, GraphQL schemas and endpoints against the OWASP API Top 10 |
| [llm-app-security](skills/llm-app-security) | Secure | Reviews LLM apps, RAG and agents against the OWASP Top 10 for LLM Applications |
| [auth-review](skills/auth-review) | Secure | Reviews OAuth/OIDC flows, JWT validation, sessions, MFA and RBAC/ABAC logic |
| [cicd-pipeline-builder](skills/cicd-pipeline-builder) | Build | Writes GitHub Actions or GitLab CI with security gates |
| [container-security](skills/container-security) | Build | Hardens Dockerfiles and reviews image scan results |
| [pipeline-hardening](skills/pipeline-hardening) | Build | Audits existing GitHub Actions and GitLab CI for unpinned actions, injection, broad tokens and long-lived keys |
| [artifact-signing](skills/artifact-signing) | Build | Signs images and release files with cosign, adds SLSA provenance and verifies at deploy time |
| [iac-review](skills/iac-review) | Infra | Checks Terraform and CloudFormation for misconfigurations |
| [k8s-manifest-review](skills/k8s-manifest-review) | Infra | Checks pod security, RBAC, network policies and resource limits |
| [cloud-iam-review](skills/cloud-iam-review) | Infra | Finds over-privileged roles and enforces least privilege |
| [policy-as-code](skills/policy-as-code) | Compliance | Writes OPA/Rego or Kyverno rules, maps controls to SOC 2, ISO 27001, PCI |
| [release-checklist](skills/release-checklist) | Deploy | Covers versioning, CI checks, feature flags and rollback plans |
| [observability-setup](skills/observability-setup) | Operate | Sets up logs, metrics, traces, alerts and SLOs without leaking PII |
| [incident-response](skills/incident-response) | Operate | Guides triage, containment, comms and escalation |
| [incident-postmortem](skills/incident-postmortem) | Operate | Writes a blameless timeline, root cause and action items |
| [vuln-management](skills/vuln-management) | Operate | Sets fix SLAs, prioritizes with EPSS and KEV, dedupes across scanners and reports aging |

## Install

Clone the repo first:

```bash
git clone https://github.com/thisiskurubaran/DevSecOps-Skills.git
```

### Claude Code

Claude Code reads skills from a directory. No zip needed.

```bash
# Personal: available in all your projects
mkdir -p ~/.claude/skills
cp -r DevSecOps-Skills/skills/iac-review ~/.claude/skills/

# Project: shared with your team through the repo
mkdir -p .claude/skills
cp -r DevSecOps-Skills/skills/iac-review .claude/skills/
```

To install every skill at once:

```bash
cp -r DevSecOps-Skills/skills/* ~/.claude/skills/
```

Start a new session after copying. Claude picks a skill when your request
matches its description, or you can call it directly with `/iac-review`.

### claude.ai and Claude Desktop

Zip the skill folder:

```bash
cd DevSecOps-Skills/skills
zip -r iac-review.zip iac-review/
```

Then:

1. Go to **Customize > Skills**.
2. Click **+**, then **Create skill**.
3. Choose **Upload a skill** and select the zip.

The skill folder must be the top level inside the zip (`iac-review/SKILL.md`),
not a bare `SKILL.md`. Skills need code execution turned on: on individual
plans that is under **Settings > Capabilities**. On Team and Enterprise plans
an owner may need to enable skills for the organization.

Docs: [Claude Code skills](https://code.claude.com/docs/en/skills) and
[Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## Usage

Once installed, ask for the work in plain language. A few examples:

```
Review this Terraform module before I open the PR.
```
Uses `iac-review`: returns a findings table with severity, file, line, and fix.

```
Here is the Trivy output for our API image. What actually needs fixing?
```
Uses `container-security` and `sast-dast-triage`: separates real findings
from noise and ranks what is left.

```
We are adding SSO login next sprint. Threat model it.
```
Uses `threat-modeling`: draws trust boundaries and walks through STRIDE.

Each skill has an `examples/test-prompts.md` file with prompts you can use to
check that it triggers.

## Layout

```
skills/
  <skill-name>/
    SKILL.md        instructions Claude follows
    references/     longer checklists and specs (optional)
    scripts/        helper scripts the skill can run (optional)
    examples/       test prompts and samples (optional)
```

## Contributing

Fixes, new checks, and new skills are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) for the skill format, style rules, and
commit format. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

Found a security problem? See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
