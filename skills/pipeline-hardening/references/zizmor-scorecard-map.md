# zizmor audits and Scorecard checks

Use these IDs in findings so readers can look up the rule and add an inline ignore with the right name. Audit names change between releases; confirm with `zizmor --help` and the docs at docs.zizmor.sh for your version. Scorecard check names are stable but scoring changes; see the checks list in the ossf/scorecard repo.

## zizmor (GitHub Actions)

| Checklist item | zizmor audit | Needs `--gh-token` |
|---|---|---|
| `pull_request_target`, `workflow_run` and other privileged triggers | dangerous-triggers | no |
| `${{ }}` expressions expanded inside `run:` or `github-script` | template-injection | no |
| Writes to `$GITHUB_ENV` / `$GITHUB_PATH` from untrusted input | github-env | no |
| Broad or missing `permissions:` | excessive-permissions | no |
| `actions/checkout` persisting the token to disk | artipacked | no |
| `uses:` not pinned to a SHA | unpinned-uses | no |
| Container `image:` not pinned by digest | unpinned-images | no |
| SHA pin that only exists on a fork of the action | impostor-commit | yes |
| Ref that is both a tag and a branch | ref-confusion | yes |
| Pinned action version has a GHSA advisory | known-vulnerable-actions | yes |
| SHA pin whose version comment no longer matches | stale-action-refs | yes |
| Cache restored in a release or publish job | cache-poisoning | no |
| Self-hosted runner in use | self-hosted-runner | no (auditor persona) |
| `secrets: inherit` on reusable workflow calls | secrets-inherit | no |
| `toJSON(secrets)` or whole secrets context passed around | overprovisioned-secrets | no |
| Bot checks on `github.actor` | bot-conditions | no |
| Registry credentials hardcoded in `container:` or `services:` | hardcoded-container-credentials | no |
| `ACTIONS_ALLOW_UNSECURE_COMMANDS` set | insecure-commands | no |
| Long-lived PyPI or npm token where trusted publishing works | use-trusted-publishing | no |

Inline ignore, with a reason next to it:

```yaml
- run: echo "${{ github.sha }}"  # zizmor: ignore[template-injection] sha is not attacker controlled
```

## OpenSSF Scorecard

| Checklist item | Scorecard check |
|---|---|
| Privileged triggers running PR code, script injection | Dangerous-Workflow |
| Top-level read-only token, per-job grants | Token-Permissions |
| Actions, images and installs pinned by hash | Pinned-Dependencies |
| Dependabot or Renovate updates pins | Dependency-Update-Tool |
| Release artifacts signed (hand off to `artifact-signing`) | Signed-Releases |
| Branch protection on the branch that deploys | Branch-Protection |
| Binaries committed to the repo | Binary-Artifacts |

Run locally:

```bash
export GITHUB_AUTH_TOKEN="<read-only token>"
scorecard --repo=github.com/example-org/app \
  --checks=Dangerous-Workflow,Token-Permissions,Pinned-Dependencies \
  --format=json | jq '.checks[] | {name, score, reason}'
```

## harden-runner rollout

1. Add `step-security/harden-runner` with `egress-policy: audit` as the first step of each job.
2. Run the workflow a few times and read the outbound endpoints in the job summary or the StepSecurity insights page.
3. Switch to `egress-policy: block` with `allowed-endpoints:` listing only those hosts.
4. Add `disable-sudo: true` where jobs do not need root.

Note that harden-runner on GitHub-hosted runners covers Linux jobs. For self-hosted runners check the StepSecurity docs for the supported setup.
