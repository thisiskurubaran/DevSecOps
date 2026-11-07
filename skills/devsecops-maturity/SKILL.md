---
name: devsecops-maturity
description: Assess a team's DevSecOps maturity against OWASP SAMM and the OWASP DevSecOps Maturity Model (DSOMM), score each practice from evidence found in the repo (CI config, branch protection, scanners, SBOMs, signing, secrets scanning, dependency bots, runbooks, postmortems) plus short interview answers, and produce a scorecard and a quarterly roadmap of 3 to 5 improvements per quarter mapped to the skills in this repo. Use when the user asks "how mature is our security program", wants a SAMM or DSOMM assessment, a security baseline, gap analysis or a DevSecOps roadmap for the next quarters.
---

# DevSecOps Maturity

Find out where a team really stands, then pick the few changes that cut the most risk next. Score from evidence you can point at, not from what people hope is true, and keep the roadmap short enough that a team can finish it.

## When to use

- The user asks for a maturity assessment, security baseline or gap analysis of a team, repo or platform.
- Someone mentions OWASP SAMM or DSOMM and wants a score or a target level.
- A new security lead or platform team wants a roadmap for the next two to four quarters.
- Leadership asks "what should we fix first" across the whole delivery pipeline, not for one finding.

Not for: a design-level threat model of one feature (use `threat-modeling`), mapping controls to SOC 2, ISO 27001 or PCI and writing policy rules (use `policy-as-code`), go or no-go checks for a single release (use `release-checklist`), or finding OWASP Top 10 bugs in code (use `security-audit`).

## Steps

1. Scope it. Name the unit being assessed: one repo, one product team, or a platform used by many teams. Mixing ten teams into one score hides the weak ones. Pick the model:
   - SAMM for program level questions (governance, design, operations). Five business functions, three practices each, levels 1 to 3.
   - DSOMM for pipeline and tooling questions. Dimensions such as Build and Deployment, Culture and Organization, Implementation, Information Gathering, Test and Verification, levels 1 to 4.
   - Both is fine: use SAMM practices as rows and cite DSOMM activities as evidence. Say which version you used.
2. Collect repo evidence before asking anyone anything. Run the commands in the checklist. Record each signal as present, absent or partial, with the file path, setting or command output that proves it.
3. Ask the interview questions for what a repo cannot show: training, threat modeling habits, incident handling, ownership, metrics. Keep it to 10 to 15 short questions. Ask for an artifact with each answer ("can you link the last postmortem?").
4. Score each practice. A level counts only if every lower level is also met and you can cite evidence for it. If the only evidence is "we do that", score the level below and mark it "claimed, not verified".
5. Set target levels. Not every practice needs level 3. Pick targets from the team's risk: internet-facing payments code needs more than an internal batch job. Most teams should aim for level 1 everywhere before level 2 anywhere.
6. List candidate improvements. One per gap, written as a concrete change ("enable secret scanning push protection on all repos"), not a theme ("improve secrets hygiene").
7. Rank by risk reduction over effort. Rate each as high, medium or low on both. Do high reduction and low effort first. Things that block other work (an SBOM before vuln tracking, CI before any gate) go early.
8. Build the roadmap. 3 to 5 items per quarter, two to four quarters. Each item gets an owner role, a done criterion that can be checked in the repo, and the skill from this repo that helps do it.
9. Write the output. Store it as `docs/security/maturity-<yyyy-qn>.md` so the next assessment can diff against it.

## Checklist

Repo evidence (run from the repo root, adjust for the platform):

- CI exists and runs on PRs: `ls .github/workflows .gitlab-ci.yml Jenkinsfile azure-pipelines.yml 2>/dev/null`.
- Branch protection and required reviews: `gh api repos/{owner}/{repo}/branches/main/protection` (404 means none), or `gh api repos/{owner}/{repo}/rulesets`. Check for required status checks and required reviewers.
- Owners: `CODEOWNERS` in the root, `.github/` or `docs/`.
- SAST: `grep -rlE 'codeql|semgrep|sonar|bandit|gosec|brakeman' .github .gitlab-ci.yml 2>/dev/null`.
- Dependency scanning and update bots: `.github/dependabot.yml`, `renovate.json`, `.renovaterc`, or `trivy fs`, `osv-scanner`, `npm audit`, `pip-audit` in CI.
- Secrets scanning: gitleaks or trufflehog in CI or pre-commit (`.pre-commit-config.yaml`, `.gitleaks.toml`). For GitHub: `gh api repos/{owner}/{repo} --jq .security_and_analysis`.
- SBOM: `syft`, `cdxgen`, `cyclonedx`, `spdx`, or `anchore/sbom-action` in workflows; SBOM files attached to releases.
- Signing and provenance: `cosign`, `attest-build-provenance`, `slsa-github-generator`, `--provenance` on npm publish.
- Action pinning: `grep -rnE 'uses: [^ ]+@(v?[0-9]+|main|master)$' .github/workflows` finds tag or branch refs instead of full commit SHAs. Check `permissions:` blocks too.
- IaC scanning: checkov, trivy config, tfsec, kics or conftest in CI when `*.tf`, CloudFormation or Kubernetes YAML exists.
- Container scanning: trivy image or grype in CI; base images pinned by digest.
- DAST: ZAP, nuclei or similar against a staging target.
- Runbooks and postmortems: `docs/runbooks/`, `docs/postmortems/`, `SECURITY.md`, an on-call link.
- Threat models: `docs/threat-models/` or design docs with a security section.
- Runtime detection: Falco, Tetragon, GuardDuty or a SIEM pipeline referenced in IaC or Helm values.

Interview questions (pick the ones the repo did not answer):

- Who owns security decisions for this team, by role?
- When did developers last get security training, and was it specific to your stack?
- Which features in the last six months got a threat model? Link one.
- How long does a critical CVE in a dependency take to fix, from alert to deploy?
- Is there a vuln SLA, and who sees breaches of it?
- Walk me through the last security incident. Is there a written postmortem with action items, and were they closed?
- Who can deploy to production, and how is that access granted and removed?
- How are production secrets stored and rotated?
- What security metrics, if any, does anyone look at monthly?

Scoring rules:

- No evidence, no level. "Claimed" is recorded but does not count.
- A scanner that runs but never fails the build and whose results nobody reads is partial at best.
- Level 2 requires level 1. Do not score a team at level 2 for SBOMs if dependency scanning is missing.
- Score the weakest repo in scope, or score repos separately. Do not average.

Roadmap rules:

- 3 to 5 items per quarter. A 20 item roadmap gets nothing done and teaches the team that the roadmap is fiction.
- Every item has a done check someone can verify in the repo or a settings page.
- Map each item to an existing skill. If no skill fits, say so instead of inventing one.

The full practice list, evidence signals per level and skill mapping are in [references/practice-map.md](references/practice-map.md).

## Output format

Start with one paragraph: scope, model and version, date, who was interviewed (by role), and anything you could not check.

Scorecard:

| Practice | Current level | Evidence | Target level | Next action | Skill |
|---|---|---|---|---|---|
| Implementation / Secure Build | 1 | `.github/workflows/ci.yml` builds on PR; 14 of 16 actions pinned by tag, not SHA; no SBOM | 2 | Pin actions to SHAs, set `permissions: contents: read`, generate CycloneDX SBOM | `pipeline-hardening`, `dependency-supply-chain` |
| Verification / Security Testing | 0 | No SAST or DAST in CI; team says "we run Snyk locally" (claimed, not verified) | 1 | Add Semgrep on PRs, block on high | `sast-dast-triage` |
| Operations / Incident Management | 1 | `docs/runbooks/` exists; no postmortems in 12 months despite two incidents named in interview | 2 | Write postmortems for both, track action items | `incident-postmortem` |

Quarterly roadmap:

| Quarter | Improvement | Risk reduction | Effort | Owner role | Done when | Skill |
|---|---|---|---|---|---|---|
| Q1 | Enable secret scanning with push protection | High | Low | Platform lead | Setting on for all repos in scope; gitleaks in pre-commit | `secrets-management` |

After the tables:

1. Top three risks in plain words, each tied to a scorecard row.
2. What was claimed but not verified, and what evidence would settle it.
3. When to reassess (usually every two quarters).

## Examples

Bad assessment: scores without evidence and a roadmap nobody can finish.

```
Governance: 3/3 (team follows best practices)
Design: 2/3
Implementation: 3/3 (we use security tools)
Verification: 2/3
Operations: 3/3

Roadmap Q1: SBOM, signing, SAST, DAST, IAST, fuzzing, threat models for
all services, training, bug bounty, SOC 2, zero trust, runtime detection,
chaos engineering, secrets vault, policy as code, red team, SIEM, ...
(22 items)
```

Problems: function-level scores with no practice rows, no evidence, level 3 claimed with no metrics, and 22 items in one quarter with no owners or done checks.

Good assessment: one row per practice, evidence cited, short ranked roadmap.

```
Scope: payments-api repo, SAMM v2 practices, DSOMM activities as evidence.
Interviewed: tech lead, on-call engineer. Could not check: SIEM config.

| Practice | Current | Evidence | Target | Next action | Skill |
| Implementation / Secure Build | 1 | ci.yml runs on PR; actions on tags; no SBOM | 2 | SHA-pin actions, add SBOM | pipeline-hardening, dependency-supply-chain |
| Implementation / Secure Deployment | 1 | deploy.yml uses OIDC; images unsigned | 2 | cosign keyless sign, verify in admission | artifact-signing |
| Design / Threat Assessment | 0 | no docs/threat-models/; lead confirms none | 1 | threat model the refund flow | threat-modeling |

Q1 (4 items, ranked)
1. Secret scanning push protection        High / Low    secrets-management
2. SHA-pin actions, least-privilege token High / Low    pipeline-hardening
3. SBOM on every release                  Med  / Low    dependency-supply-chain
4. Threat model refund flow               High / Med    threat-modeling
Q2: signing and verify at deploy, Semgrep blocking on high, first postmortem template.
```
