---
name: pipeline-hardening
description: Audit existing GitHub Actions workflows and GitLab CI pipelines for supply chain and privilege risks (unpinned actions, pull_request_target and workflow_run abuse, script injection from github.event fields, long-lived cloud keys instead of OIDC, broad GITHUB_TOKEN permissions, self-hosted runner exposure, cache poisoning, untrusted artifacts) using zizmor, actionlint, OpenSSF Scorecard and harden-runner, and return a findings table with fixed YAML. Use when the user asks to audit, harden or security-review the CI/CD workflows already in a repo, shares zizmor or Scorecard output, or asks whether a workflow can be exploited from a fork PR.
---

# Pipeline Hardening

Audit the pipelines a repo already has. A CI workflow holds deploy credentials, write tokens and runner access, and it runs code from people you do not control. The goal is to find every path where a fork PR, an issue comment or a compromised third-party action can reach those, and close it with the smallest YAML change.

## When to use

- The user asks for a security audit of `.github/workflows/*.yml`, `action.yml` files or `.gitlab-ci.yml`.
- The user shares zizmor, actionlint or OpenSSF Scorecard output and wants it explained and fixed.
- A workflow uses `pull_request_target`, `workflow_run`, `issue_comment` or self-hosted runners and someone asks if it is safe.
- After a supply chain incident (a compromised action or tag), the user wants to know if their pipelines are exposed.

Not for: writing a new pipeline from scratch or adding scan stages (use `cicd-pipeline-builder`), rotating or moving leaked secrets into a vault (use `secrets-management`), or setting up cosign, SLSA provenance and signature verification for release artifacts (use `artifact-signing`). Flag those gaps here and hand off.

## Steps

1. Inventory. List every workflow file, composite action, reusable workflow (`uses: ./.github/workflows/...` or `org/repo/.github/workflows/x.yml@ref`) and GitLab include. For each, note triggers, runners, secrets used and what it can write to (repo, packages, cloud, registry).
2. Run the scanners where possible:
   - `zizmor --format plain .github/workflows/` (add `--gh-token` for online audits such as `impostor-commit` and `known-vulnerable-actions`; use `--persona auditor` for a stricter pass).
   - `actionlint` for syntax, expression and shellcheck errors that hide bugs.
   - `scorecard --repo=github.com/example-org/app --checks=Dangerous-Workflow,Token-Permissions,Pinned-Dependencies` or read the Scorecard SARIF if the repo runs the action.
   - GitLab has no zizmor equivalent; read the YAML by hand against the checklist and use `glab ci lint` for syntax.
3. Rank triggers by trust. `pull_request` from forks gets a read-only token and no secrets. `pull_request_target`, `workflow_run`, `issue_comment` and `discussion` run in the base repo context with secrets. Any job on those triggers that checks out or executes PR code is the first thing to fix.
4. Trace untrusted input. Find every `${{ github.event.* }}`, `${{ github.head_ref }}` and `${{ inputs.* }}` used inside `run:`, `script:` (actions/github-script) or written to `$GITHUB_ENV` / `$GITHUB_OUTPUT`. Titles, bodies, branch names, commit messages and labels are attacker controlled.
5. Check identity and tokens. Top-level `permissions:` should be `contents: read` or `{}`, with per-job grants. Look for static cloud keys in `secrets.*` and replace them with OIDC (`id-token: write`) plus a cloud trust policy pinned to repo, branch or environment.
6. Check what runs. Every `uses:` pinned to a 40-character SHA with a version comment. Container `image:` pinned by digest. No `curl | bash` installers without a checksum.
7. Check runners. Self-hosted runners must not serve public repos or fork PRs. Prefer ephemeral runners (`--ephemeral`, ARC, or cloud autoscalers) so one job cannot persist into the next.
8. Check caches and artifacts. Caches written by untrusted jobs must not be restored by release jobs. Artifacts downloaded in a privileged `workflow_run` job are untrusted input: extract to a temp dir, validate, never execute.
9. Propose runtime controls. Add `step-security/harden-runner` with `egress-policy: audit` first, then `block` with an allowlist once the endpoints are known.
10. Write fixes as YAML, drop false positives with a reason (zizmor supports `# zizmor: ignore[rule-id]` inline), and report with the output format.

## Checklist

Triggers:

- No `pull_request_target` job that checks out `github.event.pull_request.head.sha`, `head.ref` or `refs/pull/*/merge` and then builds, tests or installs.
- `workflow_run` jobs treat downloaded artifacts and `github.event.workflow_run.head_branch` as untrusted.
- `issue_comment` triggered jobs check `github.event.comment.author_association` (OWNER, MEMBER, COLLABORATOR) before doing anything privileged.
- Bot checks use `github.event.pull_request.user.login`, not `github.actor`, which changes on re-runs.

Script injection:

- No `${{ github.event.issue.title }}`, `.body`, `.pull_request.head.ref`, `.head_commit.message`, `.review.body` or similar inside `run:` or `github-script`. Pass through `env:` and quote: `"$TITLE"`.
- Nothing attacker controlled is appended to `$GITHUB_ENV` or `$GITHUB_PATH` (zizmor `github-env`).
- GitLab: `$CI_COMMIT_MESSAGE`, `$CI_COMMIT_BRANCH` and `$CI_MERGE_REQUEST_TITLE` are quoted and never passed to `eval`.

Tokens and credentials:

- Top-level `permissions:` set; no `write-all`; write scopes granted per job and justified.
- `actions/checkout` uses `persist-credentials: false` unless a later step pushes (zizmor `artipacked`).
- No `AWS_ACCESS_KEY_ID`, `AZURE_CREDENTIALS` JSON or GCP service account key in secrets for deploy; use OIDC (`aws-actions/configure-aws-credentials`, `google-github-actions/auth`, `azure/login`, GitLab `id_tokens:`).
- OIDC trust policy `sub` condition names the repo and a branch or environment, not `repo:example-org/*`.
- Reusable workflows get named secrets, not `secrets: inherit`.
- GitLab: protected variables only, masked, and not exposed to merge request pipelines from forks.

Third-party code:

- Every `uses:` pinned to a full SHA that exists on the upstream repo (zizmor `impostor-commit`), with `# vX.Y.Z` comment.
- Dependabot or Renovate updates `github-actions` so pins do not go stale.
- Actions with known advisories flagged (zizmor `known-vulnerable-actions`).
- GitLab `include: project:` pinned with `ref:` to a SHA or protected tag; `include: remote:` avoided.

Runners:

- Public repos do not use self-hosted runners, or restrict them to jobs that never run on fork events.
- Self-hosted runners are ephemeral, run in a separate network segment and have no long-lived cloud role.
- Runner groups restrict which repos and workflows can target them.

Cache and artifacts:

- Release and deploy jobs do not restore caches written by PR jobs (zizmor `cache-poisoning`); use `actions/cache/restore` with no save, or disable caching in release workflows.
- Cache keys include the lockfile hash and runner OS.
- Artifacts consumed across workflows are verified (checksum file from a trusted job, or attestation via `actions/attest-build-provenance` and `gh attestation verify`).

Runtime:

- `step-security/harden-runner` is the first step in jobs that hold secrets, with a known egress allowlist.
- `timeout-minutes` set; `concurrency` set on deploy jobs.

See [references/zizmor-scorecard-map.md](references/zizmor-scorecard-map.md) for zizmor audit IDs and Scorecard checks mapped to each item.

## Output format

| Severity | File | Line | Rule | Issue | Fix |
|---|---|---|---|---|---|
| Critical | .github/workflows/pr-test.yml | 4, 15 | dangerous-triggers | `pull_request_target` checks out PR head and runs `npm test` with `NPM_TOKEN` in env | Switch to `pull_request`; move the token step to a separate workflow that only runs on `push` to main |
| High | .github/workflows/triage.yml | 22 | template-injection | `${{ github.event.issue.title }}` inside `run:` | Pass through `env: TITLE:` and use `"$TITLE"` |
| Medium | .github/workflows/ci.yml | 9 | unpinned-uses | `actions/setup-node@v4` | Pin to SHA with `# v4.x.y` comment |

After the table:

1. Fixed YAML for each Critical and High.
2. Scanner summary: tool, version, finding counts, and which findings you marked as false positives with the reason.
3. Repo settings to change by hand: Actions "Allow GitHub Actions to create and approve pull requests" off, default workflow permissions set to read, "Require approval for all outside collaborators" on fork PRs, runner group restrictions, OIDC trust policy in the cloud account.
4. Hand-offs: leaked or long-lived keys that need rotation (`secrets-management`), unsigned release artifacts (`artifact-signing`).

Severity: Critical (untrusted code can reach secrets, write tokens, cloud roles or a self-hosted runner), High (injection path or privileged trigger that needs one more condition to exploit, static cloud keys), Medium (unpinned actions or images, broad permissions without a direct exploit path, missing egress control), Low (hygiene: missing timeouts, stale pins, lint errors).

## Examples

Bad: privileged trigger runs PR code, issue title injected into shell, tag-pinned action, static keys, shared cache.

```yaml
on:
  pull_request_target:
  issue_comment:
    types: [created]
jobs:
  test:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm
      - run: npm ci && npm test
      - run: echo "Comment: ${{ github.event.comment.body }}"
      - uses: example-org/upload-action@main
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Good: untrusted tests on `pull_request` with no secrets, privileged work only on `push` to main, OIDC, SHA pins, egress control.

```yaml
# .github/workflows/test.yml
on: pull_request
permissions: {}
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: step-security/harden-runner@0634a2670c59f64b4a01f0f96f84700a4088b9f0 # v2.12.0
        with:
          egress-policy: audit
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - run: npm ci && npm test
```

```yaml
# .github/workflows/release.yml
on:
  push:
    branches: [main]
permissions: {}
jobs:
  upload:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: step-security/harden-runner@0634a2670c59f64b4a01f0f96f84700a4088b9f0 # v2.12.0
        with:
          egress-policy: block
          allowed-endpoints: >
            github.com:443
            registry.npmjs.org:443
            sts.us-east-1.amazonaws.com:443
            s3.us-east-1.amazonaws.com:443
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - run: npm ci && npm run build
      - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-release-app
          aws-region: us-east-1
      - name: Upload
        env:
          COMMIT_MSG: ${{ github.event.head_commit.message }}
        run: |
          echo "Uploading build for: $COMMIT_MSG"
          aws s3 sync dist/ s3://example-app-releases/
```

The SHAs above are illustrative. Look up the current SHA for each action's release tag before committing, and confirm it is on the upstream repo, not a fork.

GitLab, bad vs good: unquoted MR title in a shell, unpinned remote include.

```yaml
# Bad
include:
  - remote: https://example.com/ci/templates.yml
notify:
  script:
    - eval "echo $CI_MERGE_REQUEST_TITLE"

# Good
include:
  - project: example-org/ci-templates
    ref: 3f2c1a9e8b7d6c5f4e3a2b1c0d9e8f7a6b5c4d3e
    file: /templates/build.yml
notify:
  script:
    - printf 'MR: %s\n' "$CI_MERGE_REQUEST_TITLE"
```
