---
name: cicd-pipeline-builder
description: Write or harden GitHub Actions workflows and GitLab CI pipelines with security gates (secret scanning, SAST, dependency and image scans, IaC checks), pinned actions, least-privilege tokens and OIDC cloud auth. Use when the user asks to create, fix or review a .github/workflows/*.yml or .gitlab-ci.yml file, add security scanning to CI, or lock down a pipeline that deploys.
---

# CI/CD Pipeline Builder

Write pipelines that build, test and ship, and that fail early when a secret, a known CVE or a bad config shows up. Treat the pipeline itself as an attack surface: it holds deploy credentials and runs code from pull requests.

## When to use

- The user wants a new GitHub Actions workflow or `.gitlab-ci.yml` for a repo.
- The user wants to add security gates (gitleaks, Semgrep, Trivy, Checkov) to an existing pipeline.
- A workflow uses long-lived cloud keys, `pull_request_target`, unpinned actions or `permissions: write-all` and needs fixing.
- A PR touches `.github/workflows/`, `.gitlab-ci.yml`, or reusable workflow files.

Not for: triaging the findings the scanners produce (use `sast-dast-triage`), hardening the Dockerfile the pipeline builds (use `container-security`), or reviewing the Terraform it applies (use `iac-review`). Release versioning and rollback plans go to `release-checklist`.

## Steps

1. Read the repo. Find the language, package manager, lockfile, test command, Dockerfile, IaC folders and deploy target. Check for existing workflows so you extend them instead of duplicating.
2. Pick the platform. GitHub Actions if the repo is on GitHub, GitLab CI if there is a `.gitlab-ci.yml` or the user says so. Do not mix.
3. Sketch the stages: `lint` and `test`, then `security` (secrets, SAST, SCA, IaC), then `build` (image plus image scan, SBOM), then `deploy` (protected, main only). Security jobs run on every PR.
4. Set token scope. In GitHub Actions put `permissions: contents: read` at the top level and grant extra scopes per job only where needed (`id-token: write` for OIDC, `packages: write` for GHCR, `security-events: write` for SARIF upload).
5. Pin third-party actions to a full commit SHA with the version in a comment. First-party `actions/*` should also be pinned in repos with strict policy. Add Dependabot or Renovate config for `github-actions` so the pins get updated.
6. Replace static cloud keys with OIDC: `aws-actions/configure-aws-credentials` with `role-to-assume`, `google-github-actions/auth` with workload identity, or `azure/login` with federated credentials. In GitLab use `id_tokens:` with an `aud`.
7. Add the gates. Decide which fail the build (high and critical) and which only report. Upload SARIF to code scanning on GitHub, or use GitLab's report artifacts, so findings show on the PR.
8. Protect deploys. Use GitHub `environment:` with required reviewers, or GitLab protected environments and `rules:` limited to the default branch. Never deploy from a fork PR.
9. Handle untrusted input. Do not interpolate `${{ github.event.* }}` fields (titles, branch names, comment bodies) straight into `run:`. Pass them through `env:` and quote them.
10. Validate. Run `actionlint` on GitHub workflows and `zizmor` for security issues. For GitLab, use the CI Lint API or `glab ci lint`. Fix every warning or explain why it stays.

## Checklist

Tokens and triggers:

- Top-level `permissions:` block exists and defaults to `contents: read`.
- No `pull_request_target` that checks out `github.event.pull_request.head.sha` and runs its code.
- `workflow_run` and `issue_comment` triggers do not run PR code with secrets.
- `actions/checkout` has `persist-credentials: false` unless a later step pushes.
- GitLab: secrets are masked and protected, and protected variables only reach protected branches.

Supply chain:

- Every `uses:` points to a 40-character SHA, not `@v4` or `@main`.
- Docker base images in CI jobs pinned by digest (`image: node:20@sha256:...`).
- Dependency installs use the lockfile: `npm ci`, `pip install --require-hashes -r requirements.txt`, `go mod download` with `GOFLAGS=-mod=readonly`.
- Caches keyed on lockfile hash, not shared across fork PRs.

Security gates:

- Secrets: `gitleaks/gitleaks-action` or `gitleaks detect --redact --exit-code 1`, or `trufflehog git file://. --only-verified --fail`.
- SAST: `semgrep scan --config p/default --error --sarif -o semgrep.sarif`, or CodeQL via `github/codeql-action/init` and `analyze`.
- SCA: `trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 .`, `osv-scanner -r .`, or `npm audit --audit-level=high`.
- IaC: `checkov -d infra/ --quiet --compact` or `trivy config --exit-code 1 infra/`.
- Image: `trivy image --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed $IMAGE` after build, before push to the release tag.
- SBOM and signing: `syft $IMAGE -o spdx-json`, `cosign sign --yes $IMAGE@$DIGEST` with keyless OIDC.

Deploy:

- Cloud auth through OIDC, trust policy pinned to repo and branch (`repo:org/app:ref:refs/heads/main`).
- `environment: production` with required reviewers, or GitLab `environment:` plus `when: manual` on protected branches.
- `concurrency:` group on deploy jobs so two runs cannot deploy at once.
- `timeout-minutes:` set on every job.

See [references/gate-matrix.md](references/gate-matrix.md) for a per-language table of scanners and their fail flags.

## Output format

When writing a pipeline, deliver:

1. The full workflow file(s) with a path header, ready to commit.
2. A short table of gates:

| Stage | Tool | Fails build on | Report location |
|---|---|---|---|
| security | gitleaks | any finding | job log, SARIF |
| security | semgrep | ERROR severity | code scanning |

3. A list of repo settings the user must change by hand (environments, branch protection, OIDC role in the cloud account).

When reviewing a pipeline, use a findings table:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| High | .github/workflows/ci.yml | 12 | `pull_request_target` checks out PR head and runs `npm test` with secrets | Switch to `pull_request`, or split into an unprivileged build and a `workflow_run` job that only reads artifacts |

Severity: Critical (secret or deploy credential reachable by untrusted code), High (privilege or injection path), Medium (missing gate, unpinned action), Low (hygiene).

## Examples

Bad: broad token, tag-pinned action, static AWS keys, script injection.

```yaml
on: [pull_request_target]
permissions: write-all
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: echo "Building ${{ github.event.pull_request.title }}"
      - uses: some-org/deploy-action@main
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Good: read-only default, SHA pins, gates on PR, OIDC deploy from main behind an environment.

```yaml
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  security:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
          fetch-depth: 0
      - name: gitleaks
        run: docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:v8.21.2 detect --source /repo --redact --exit-code 1
      - name: semgrep
        run: pipx run semgrep scan --config p/default --error
      - name: trivy fs
        run: docker run --rm -v "$PWD:/src" aquasec/trivy:0.57.1 fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 /src
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: security
    runs-on: ubuntu-latest
    environment: production
    concurrency: deploy-production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-deploy-app
          aws-region: us-east-1
      - name: Log commit message safely
        env:
          TITLE: ${{ github.event.head_commit.message }}
        run: echo "Deploying: $TITLE"
```

The SHAs above are illustrative. Look up the current SHA for each action's release tag before committing.
