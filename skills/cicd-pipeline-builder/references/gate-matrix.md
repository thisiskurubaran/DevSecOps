# Security gate matrix

Pick one tool per row. Commands assume the tool is on the runner's PATH or run from its official container image.

## Secrets

| Tool | Command | Fails on |
|---|---|---|
| gitleaks | `gitleaks detect --source . --redact --exit-code 1` | any finding |
| gitleaks (PR diff only) | `gitleaks detect --log-opts="origin/main..HEAD" --redact` | any finding in new commits |
| trufflehog | `trufflehog git file://. --since-commit main --only-verified --fail` | verified live secrets |

## SAST

| Language | Tool | Command |
|---|---|---|
| Any | Semgrep | `semgrep scan --config p/default --error --sarif -o semgrep.sarif` |
| JS/TS, Python, Go, Java, C#, Ruby | CodeQL | `github/codeql-action/init` + `autobuild` + `analyze` |
| Python | Bandit | `bandit -r src -ll -f sarif -o bandit.sarif` |
| Go | gosec | `gosec -fmt sarif -out gosec.sarif ./...` |

## Dependencies (SCA)

| Ecosystem | Tool | Command |
|---|---|---|
| Any lockfile | Trivy | `trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 .` |
| Any lockfile | OSV-Scanner | `osv-scanner scan -r .` |
| npm | npm audit | `npm audit --audit-level=high --omit=dev` |
| Python | pip-audit | `pip-audit -r requirements.txt --strict` |
| Go | govulncheck | `govulncheck ./...` |

## IaC

| Target | Tool | Command |
|---|---|---|
| Terraform, CFN, k8s, Dockerfile | Checkov | `checkov -d . --quiet --compact -o sarif` |
| Terraform | tfsec (now in Trivy) | `trivy config --severity HIGH,CRITICAL --exit-code 1 infra/` |
| Kubernetes | kube-score | `kube-score score k8s/*.yaml --output-format ci` |
| Workflows | zizmor | `zizmor .github/workflows/` |

## Images

| Step | Tool | Command |
|---|---|---|
| Scan | Trivy | `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 $IMAGE` |
| Scan | Grype | `grype $IMAGE --fail-on high` |
| SBOM | Syft | `syft $IMAGE -o spdx-json=sbom.spdx.json` |
| Sign | Cosign | `cosign sign --yes $IMAGE@$DIGEST` |
| Attest | Cosign | `cosign attest --yes --predicate sbom.spdx.json --type spdxjson $IMAGE@$DIGEST` |

## GitLab equivalents

GitLab ships templates you can include instead of hand-writing jobs:

```yaml
include:
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml
  - template: Jobs/SAST-IaC.gitlab-ci.yml
```

Some of these need GitLab Ultimate to show results in the merge request widget. On lower tiers, run the open source tools directly and publish their reports as artifacts.

## What should fail the build

- Any verified secret.
- Critical and high CVEs with a fix available.
- High SAST findings from rules with a low false positive rate.
- IaC checks for public storage, open security groups, disabled encryption.

Report only (do not fail) at first: medium CVEs, unfixed CVEs, style-level SAST rules. Tighten after the backlog is cleared.
