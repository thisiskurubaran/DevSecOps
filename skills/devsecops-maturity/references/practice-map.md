# Practice map: SAMM, DSOMM, evidence and skills

Use this file to turn repo evidence into a level and a level gap into a skill. Level descriptions here are short working summaries for scoring, not the official model text. Check the model pages for the exact wording before you publish a score:

- OWASP SAMM: https://owaspsamm.org/model/
- OWASP DSOMM: https://dsomm.owasp.org/

## OWASP SAMM v2

Five business functions, three security practices each. Every practice has two streams (A and B) and maturity levels 1 to 3. Score 0 when level 1 is not met.

Rough meaning of the levels across practices:

- Level 1: done ad hoc or by a few people, but it exists and you can show it.
- Level 2: defined, repeatable, applied across the team or org, with owners.
- Level 3: measured and improved, with metrics that someone acts on.

### Governance

| Practice | Level 1 evidence | Level 2 evidence | Level 3 evidence | Skills |
|---|---|---|---|---|
| Strategy and Metrics | A written security goal or roadmap exists | Roadmap reviewed on a schedule, a few metrics tracked (vuln age, SLA breaches) | Metrics drive budget and priority decisions | `devsecops-maturity`, `vuln-management` |
| Policy and Compliance | Security requirements written down somewhere | Policies mapped to controls, checked in CI or by audit | Compliance checked continuously, exceptions tracked to expiry | `policy-as-code`, `risk-acceptance` |
| Education and Guidance | Some developers had security training | Role and stack specific training, secure coding guide in the repo | Security champions per team, training tied to findings | `project-conventions`, `docs-writer` |

### Design

| Practice | Level 1 evidence | Level 2 evidence | Level 3 evidence | Skills |
|---|---|---|---|---|
| Threat Assessment | Threat models exist for some features | Threat model required for new services or boundary changes, stored in repo | Threat models updated after incidents, reused patterns | `threat-modeling` |
| Security Requirements | Security requirements in some tickets or specs | Standard requirements per feature type, supplier security checks | Requirements traced to tests | `threat-modeling`, `api-security-review`, `privacy-review` |
| Security Architecture | Known good components and patterns named | Shared reference architectures and approved libraries | Architecture checked against the reference, drift tracked | `project-conventions`, `auth-review`, `crypto-review` |

### Implementation

| Practice | Level 1 evidence | Level 2 evidence | Level 3 evidence | Skills |
|---|---|---|---|---|
| Secure Build | Automated, repeatable build in CI | Pinned dependencies and actions, SBOM per build, build fails on known bad components | Signed provenance, hermetic or reproducible builds | `cicd-pipeline-builder`, `pipeline-hardening`, `dependency-supply-chain`, `artifact-signing` |
| Secure Deployment | Automated deploy, no manual copy to prod | Secrets from a vault or KMS, deploy access limited, signed images | Integrity verified at deploy (admission checks), GitOps with review | `secrets-management`, `artifact-signing`, `gitops-security`, `release-checklist` |
| Defect Management | Security findings tracked somewhere | Severity based SLAs, owners, dedupe across scanners | Defect metrics reviewed and drive training or design changes | `vuln-management`, `sast-dast-triage`, `risk-acceptance` |

### Verification

| Practice | Level 1 evidence | Level 2 evidence | Level 3 evidence | Skills |
|---|---|---|---|---|
| Architecture Assessment | Ad hoc security review of architecture | Review against a checklist or threat model for key services | Findings feed back into reference architectures | `threat-modeling`, `cloud-iam-review` |
| Requirements-driven Testing | Some security tests written for known risks | Tests for each security requirement, regression tests for past bugs | Abuse case tests run in CI and are measured | `test-generator`, `security-audit` |
| Security Testing | SAST or DAST run at least occasionally | Automated scans in CI with a blocking threshold, manual review of risky changes | Scans tuned per app, pen tests feed back into scanner rules | `sast-dast-triage`, `dast-setup`, `security-audit`, `code-review` |

### Operations

| Practice | Level 1 evidence | Level 2 evidence | Level 3 evidence | Skills |
|---|---|---|---|---|
| Incident Management | Someone is on call, incidents get handled | Written runbooks, roles, postmortems with action items | Detection tuned from postmortems, incident metrics tracked | `incident-response`, `incident-postmortem`, `runtime-security`, `detection-engineering` |
| Environment Management | Systems patched, configs hardened in places | Hardening baselines in IaC, scanners on IaC and images | Drift detection and posture scans with tracked fixes | `iac-review`, `container-security`, `k8s-manifest-review`, `helm-review`, `cspm-triage`, `security-headers` |
| Operational Management | Logs exist, data has an owner | Central logging, data classification, retention rules | Logging and data handling audited, PII kept out of telemetry | `observability-setup`, `privacy-review` |

## OWASP DSOMM

DSOMM groups activities into dimensions and sub-dimensions. Levels run 1 to 4 in the versions most teams cite; check the site, since the model is updated often. Use DSOMM activities as concrete evidence under the SAMM rows above, or score DSOMM directly for pipeline focused teams.

| Dimension | Sub-dimensions | Typical evidence | Skills |
|---|---|---|---|
| Build and Deployment | Build, Deployment, Patch Management | CI on every PR, pinned images and actions, SBOM, signing, automated dependency PRs merged on a schedule | `cicd-pipeline-builder`, `pipeline-hardening`, `artifact-signing`, `dependency-supply-chain`, `gitops-security` |
| Culture and Organization | Design, Education and Guidance, Process | Threat models, training records, security champions, defined process for findings | `threat-modeling`, `project-conventions`, `vuln-management` |
| Implementation | Application Hardening, Development and Source Control, Infrastructure Hardening | Branch protection, CODEOWNERS, signed commits, hardened containers and IaC, security headers | `container-security`, `iac-review`, `k8s-manifest-review`, `security-headers`, `code-review` |
| Information Gathering | Logging, Monitoring, Test KPI | Central logs, alerts on security events, scanner metrics tracked over time | `observability-setup`, `runtime-security`, `detection-engineering`, `vuln-management` |
| Test and Verification | Application Tests, Consolidation, Static and dynamic depth for applications and infrastructure, Test-Intensity | SAST, DAST, IaC and image scans in CI, findings consolidated in one tracker | `sast-dast-triage`, `dast-setup`, `iac-review`, `container-security`, `vuln-management` |

## Gap to skill mapping

| Gap found | Signal | Skill |
|---|---|---|
| No secrets scanning | No gitleaks or trufflehog in CI or pre-commit; GitHub secret scanning off | `secrets-management` |
| Secrets in env files or CI variables without rotation | Long-lived keys in workflow `env:`, `.env` history | `secrets-management` |
| Unpinned actions, broad token | `uses: org/action@v3`, no `permissions:` block, `pull_request_target` | `pipeline-hardening` |
| No CI or no security gates | No workflow files, or no scan step that can fail | `cicd-pipeline-builder` |
| No SBOM, no dependency scanning | No syft or cdxgen, no Dependabot or Renovate | `dependency-supply-chain` |
| Unsigned images or releases | No cosign or attestation steps, images deployed by tag | `artifact-signing` |
| No threat models | No `docs/threat-models/`, design docs without a security section | `threat-modeling` |
| No SAST or findings ignored | No CodeQL or Semgrep, or results never block | `sast-dast-triage` |
| No DAST | Nothing scans a running staging app | `dast-setup` |
| No vuln SLAs or backlog tracking | Findings live only in scanner UIs | `vuln-management` |
| Exceptions with no expiry | Suppressions with no reason or date | `risk-acceptance` |
| IaC not scanned | `*.tf` or CloudFormation with no checkov or trivy config in CI | `iac-review` |
| Cloud posture unknown | No Prowler, Security Hub or similar results reviewed | `cspm-triage` |
| Over-privileged cloud roles | `*` actions, admin roles on CI | `cloud-iam-review` |
| Containers run as root, unpinned bases | Dockerfile without `USER`, `FROM image:latest` | `container-security` |
| Pod security, RBAC gaps | No securityContext, no NetworkPolicy | `k8s-manifest-review`, `helm-review` |
| GitOps without review or drift checks | Argo CD or Flux syncing from unprotected branches | `gitops-security` |
| No postmortems | Incidents named in interview, no written postmortem | `incident-postmortem` |
| No incident runbooks | No `docs/runbooks/`, no on-call path for security events | `incident-response` |
| No runtime detection | No Falco, Tetragon, GuardDuty or SIEM rules | `runtime-security`, `detection-engineering` |
| Logs missing or full of PII | No central logging, tokens or emails in log lines | `observability-setup`, `privacy-review` |
| Weak or custom crypto | Hand-rolled crypto, MD5 or SHA-1 for passwords | `crypto-review` |
| Missing HTTP security headers | No CSP, HSTS or frame protection on web apps | `security-headers` |
| Auth and API gaps | Missing authz checks, no rate limits | `auth-review`, `api-security-review` |
| LLM features with no review | Prompts built from user input, tools with broad access | `llm-app-security` |
| Compliance control mapping needed | Auditor asks for SOC 2 or ISO 27001 evidence | `policy-as-code` |
| No release gate | Releases cut by hand with no checklist or rollback plan | `release-checklist` |

If a gap has no matching skill in `skills/`, write "no skill yet" in the Skill column rather than naming one that does not exist.
