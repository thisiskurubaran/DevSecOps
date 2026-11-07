# Dedupe keys and priority scoring

Detail for steps 3 and 4 of the skill. Adjust the thresholds to your policy, but write down whatever you pick so the numbers can be recomputed.

## Dedupe keys

| Finding type | Key | Example sources |
|---|---|---|
| Dependency CVE | vuln ID + ecosystem + package + asset | Trivy fs, Snyk Open Source, Dependabot, `npm audit`, `pip-audit`, OSV-Scanner |
| Container CVE | vuln ID + package + base image digest | Trivy image, Grype, Snyk Container, ECR or GCR scanning |
| Code weakness | CWE + repo + file + line range or function | Semgrep, CodeQL, SonarQube, Snyk Code |
| DAST | CWE or plugin + host + path + parameter | ZAP, Burp, Nuclei |
| IaC | normalized check + resource address | Checkov, Trivy config, tfsec |

Notes:

- Normalize vuln IDs first. A GHSA and a CVE often name the same issue. Use the OSV `aliases` field to map GHSA, PYSEC, GO and RUSTSEC IDs to one canonical ID (prefer CVE when present).
- Normalize package names: lowercase, PEP 503 for Python (`Django` and `django` match), strip `@scope/` only if your tools disagree on it.
- For code, exact line numbers drift between commits. Match on file plus enclosing function, or a line window of plus or minus 3, and confirm by CWE.
- Semgrep and CodeQL report different CWEs for the same bug sometimes (CWE-89 vs CWE-943). Keep a small alias table.
- Keep every source on the merged finding. When one scanner stops reporting it and another still does, it is not fixed.
- DefectDojo: turn on deduplication per product and set `HASHCODE_FIELDS_PER_SCANNER` for cross-tool matching, or use `DEDUPLICATION_ALGORITHM_PER_PARSER` with `unique_id_from_tool_or_hash_code`. Test on a copy first; a bad hash config merges unrelated findings.

## Priority inputs

| Input | Where to get it | How it moves priority |
|---|---|---|
| CVSS base | NVD, GHSA, vendor advisory | Starting level: 9.0+ Critical, 7.0 to 8.9 High, 4.0 to 6.9 Medium, below 4.0 Low |
| CISA KEV | `https://www.cisa.gov/known-exploited-vulnerabilities-catalog` (JSON feed) | Listed: Critical, and use the shorter KEV due date if your policy follows BOD 22-01 |
| EPSS | `https://api.first.org/data/v1/epss?cve=CVE-2023-44487` | 0.1 or above: up one level. Below 0.01 and not on KEV: may go down one level |
| Reachability | Snyk reachable vulns, Semgrep Supply Chain, govulncheck, CodeQL data flow | Proven unreachable: down one level, attach evidence. Unknown: no change |
| Exposure | Asset inventory, ingress config, cloud security group data | Internet-facing: up one. Internal: no change. Build or test only: down one |
| Data class | Asset inventory | Regulated or customer data: floor of High for CVSS 9.0+ |

Rules:

- Cap at Critical, floor at Low. Never lower a KEV-listed finding.
- Apply at most two downgrades. A 9.8 does not become Info because it is unreachable and internal.
- Re-score when inputs change: EPSS updates daily, KEV adds entries weekly. A nightly job that refreshes both and recomputes due dates is enough.
- When priority goes up, the due date moves earlier from first seen. When it goes down, keep the original due date unless the owner asks for the new one through the exception process.

## Exception record

```yaml
finding: VM-140
requested_by: dev-lead@example.com
approved_by: security-lead@example.com
reason: lodash only used in build tooling, not shipped to browsers
compensating_control: CI blocks lodash in production bundle (bundle-check job)
accepted_on: 2026-11-07
expires_on: 2027-02-05
review: re-check on expiry or if lodash appears in runtime dependencies
```
