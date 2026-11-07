---
name: dependency-supply-chain
description: Review third-party dependencies for known CVEs, reachability, license conflicts and supply chain risk (typosquats, unpinned versions, install scripts, unsigned artifacts), and produce or check SBOMs (CycloneDX, SPDX) with upgrade plans. Use when the user shares Dependabot, Renovate, Snyk, npm audit, pip-audit, OSV-Scanner or Trivy fs output, asks about a CVE in a package, adds a new dependency, or needs an SBOM or license report.
---

# Dependency and Supply Chain Review

Most code in a service comes from other people. This skill checks what you pull in, whether its known vulnerabilities actually affect you, whether its license fits, and whether the way you fetch and build it can be tampered with.

## When to use

- SCA output needs a decision: Dependabot or Renovate PRs, `npm audit`, `pip-audit`, `osv-scanner`, `govulncheck`, Snyk Open Source, `trivy fs`, Grype on a source tree.
- Someone asks "are we affected by CVE-XXXX-YYYY?" or "is this package safe to add?"
- A customer or auditor wants an SBOM or a license report.
- A PR changes a lockfile, adds a package, or changes registry config.

Not for: findings in your own code from SAST tools (use `sast-dast-triage`), CVEs in container base image OS packages (use `container-security`), or pipeline hardening like pinning GitHub Actions in workflow files (use `cicd-pipeline-builder`, though this skill flags unpinned actions when it sees them).

## Steps

1. Find the manifests and lockfiles: `package.json` plus `package-lock.json`, `pnpm-lock.yaml` or `yarn.lock`; `requirements*.txt`, `poetry.lock`, `uv.lock`; `go.mod` and `go.sum`; `pom.xml`, `build.gradle*`; `Cargo.lock`; `Gemfile.lock`. No lockfile is a finding on its own.
2. Run a scanner that reads the lockfile:
   - Any ecosystem: `osv-scanner scan source -r .` or `trivy fs --scanners vuln,license --format json -o trivy.json .`
   - Node: `npm audit --omit=dev --json`
   - Python: `pip-audit -r requirements.txt --format json`
   - Go: `govulncheck ./...` (reports only vulnerable symbols you call)
   - Java: `mvn org.owasp:dependency-check-maven:check`, or Trivy on the jar
3. Deduplicate by package and CVE. One vulnerable transitive package often shows up under many parents.
4. For each CVE, decide if it affects you:
   - Is the vulnerable version actually resolved in the lockfile (not just allowed by the range)?
   - Is it a runtime dependency or dev or build only?
   - Is the vulnerable function reachable? Read the advisory (GHSA, OSV) for the affected API, then `grep` your code for it. `govulncheck` and Snyk reachability do this for some languages.
   - Is it exploitable in your context (network-facing, user input reaches it)?
   - Check EPSS score and CISA KEV listing for real-world exploitation.
5. Rank with the table in Output format. KEV-listed and reachable goes to the top regardless of CVSS.
6. Plan the fix. Prefer the smallest version bump that clears the CVE. For a transitive package, use `overrides` (npm), `resolutions` (Yarn), `pnpm.overrides`, a constraint in `constraints.txt`, or `replace` in `go.mod`, and note it so it gets removed later. If no fix exists, document a compensating control and a VEX statement.
7. Check licenses. Generate a list (`trivy fs --scanners license`, `npx license-checker --summary`, `pip-licenses`, `go-licenses report ./...`). Flag copyleft (GPL, AGPL, SSPL) in distributed or SaaS code per the project's policy, and packages with no license.
8. Check supply chain hygiene with the checklist: pinning, integrity hashes, registry config, install scripts, maintainers, provenance.
9. Produce or validate the SBOM: `syft dir:. -o cyclonedx-json=sbom.cdx.json` or `trivy fs --format cyclonedx -o sbom.cdx.json .`. For images, run against the image so OS packages are included. Validate with `cyclonedx validate --input-file sbom.cdx.json`.
10. Write the report and, for new packages, a short add or reject recommendation.

## Checklist

Pinning and integrity

- Lockfile committed and used in CI: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`, `pip install --require-hashes -r requirements.txt`, `poetry install --sync`, `go mod verify`.
- No `latest`, `*`, or open ranges for direct production dependencies in apps (libraries may use ranges).
- Git dependencies pinned to a commit SHA, not a branch.
- GitHub Actions pinned to a full commit SHA, with the tag in a comment.
- Base images pinned by digest (`@sha256:...`).

Registry and resolution

- Private packages use a scoped registry (`@acme:registry=` in `.npmrc`) so a public package with the same name cannot win (dependency confusion).
- pip: `--index-url` for the private index, not `--extra-index-url`, which lets PyPI win on a higher version.
- No credentials in committed `.npmrc` or `pip.conf`. Use env vars or CI secrets.

Package risk signals for new dependencies

- Name close to a popular package (`reqeusts`, `lodahs`, `python-dateutil` vs `dateutil`)?
- Published recently, low downloads, single maintainer, maintainer recently changed?
- `preinstall`, `install` or `postinstall` scripts in `package.json`? Consider `npm ci --ignore-scripts` in CI and allow only needed ones.
- Repo link matches the published package (Sigstore provenance on npm, PyPI Trusted Publishers attestations)?
- OpenSSF Scorecard: `scorecard --repo=github.com/<owner>/<repo>`. Low scores on Maintained, Code-Review or Signed-Releases are worth a note.
- Is the package needed at all? Ten lines of your own code beats a new transitive tree.

Automation

- Dependabot or Renovate configured for every ecosystem in the repo, including `github-actions` and `docker`.
- Grouped minor and patch updates, security updates not delayed by schedule.
- CI fails on new high or critical reachable CVEs, not on every advisory (`osv-scanner` with a config ignore list that has reasons and expiry dates).

SBOM

- Format: CycloneDX 1.5+ or SPDX 2.3+.
- Includes direct and transitive components with `purl`, version and license.
- Generated in CI per release artifact and stored with the release. Signed or attested (`cosign attest --type cyclonedx`).

More detail on license policy and VEX is in [references/license-and-vex.md](references/license-and-vex.md).

## Output format

Summary line: packages scanned, CVEs found, CVEs that affect you, license issues.

### Vulnerabilities

| Priority | Package | Installed | Fixed in | CVE / GHSA | CVSS | EPSS / KEV | Runtime? | Reachable? | Action |
|----------|---------|-----------|----------|------------|------|------------|----------|------------|--------|

Priority:

| Level | Rule |
|-------|------|
| P0 | KEV-listed or public exploit, reachable, runtime. Fix today. |
| P1 | High or critical, reachable or unknown, runtime. Fix this sprint. |
| P2 | Not reachable, or dev only, or needs unusual config. Next scheduled update. |
| P3 | Low impact or no fix available. Document, VEX `not_affected` or accept with a date. |

### Licenses

| Package | Version | License | Issue | Action |

### Supply chain hygiene

| Check | File | Line | Issue | Fix |

## Examples

### Bad: open range, extra index, no hashes

```text
# requirements.txt
--extra-index-url https://pypi.internal.example.com/simple
acme-billing
requests>=2.0
pyyaml
```

`acme-billing` can be hijacked by a public PyPI package with a higher version. Nothing is pinned, so builds are not reproducible and a compromised release lands on the next deploy.

### Good: single index, pinned, hashed

```text
# requirements.txt (built by: pip-compile --generate-hashes requirements.in)
--index-url https://pypi.internal.example.com/simple
acme-billing==3.4.1 \
    --hash=sha256:0000000000000000000000000000000000000000000000000000000000000000
requests==2.32.3 \
    --hash=sha256:1111111111111111111111111111111111111111111111111111111111111111
```

The internal index proxies PyPI, so there is one source of truth. Install with `pip install --require-hashes -r requirements.txt`.

### Bad vs good: transitive fix in npm

Bad: running `npm audit fix --force`, which may jump major versions of direct dependencies and break the app.

Good: pin only the vulnerable transitive package and leave a removal note.

```json
{
  "overrides": {
    "braces": "3.0.3"
  }
}
```

Then `npm install`, run tests, and confirm with `npm ls braces` that every path resolves to 3.0.3.
