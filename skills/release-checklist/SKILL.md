---
name: release-checklist
description: Build a release checklist and go/no-go plan covering semantic versioning, changelog, green CI and security gates, signed artifacts, database migrations, feature flags, staged rollout and a tested rollback plan. Use when the user is preparing a release or deploy, cutting a tag, asks "are we ready to ship", or wants a rollback plan for a production change.
---

# Release Checklist

Get a release from "main is green" to "running in production" with no surprises, and with a way back that has been tried before it is needed.

## When to use

- The user is about to cut a version tag, publish a package, or deploy a service to production.
- The user asks for a go/no-go review, a release plan, or a rollback plan.
- A release includes a schema migration, a config change, a dependency major bump, or a feature behind a flag.
- A team wants a reusable release template for their repo.

Not for: writing the CI workflow itself (use `cicd-pipeline-builder`), writing the migration (use `migration-helper`), or writing the commit and PR text (use `commit-pr-writer`). If the release already broke production, switch to `incident-response`.

## Steps

1. Collect the change set. Run `git log --oneline <last-tag>..HEAD` and `git diff --stat <last-tag>..HEAD`. List PRs, migrations, config and infra changes, and dependency bumps.
2. Pick the version with SemVer. Breaking API or config change: major. New feature, backward compatible: minor. Fix only: patch. Under `0.x`, call out breaking changes even on a minor bump.
3. Update the changelog under the new version heading (Keep a Changelog sections: Added, Changed, Deprecated, Removed, Fixed, Security). Link CVE IDs for security fixes.
4. Confirm gates on the exact commit you will tag: tests, lint, SAST, SCA, secret scan, image scan, IaC scan. "Green on the PR" is not enough if main moved after merge.
5. Classify risk. High risk if any of: migration that rewrites or locks a large table, auth or payment code, infra change, dependency major bump, change with no flag. High risk means staged rollout and a named person on watch.
6. Plan migrations with expand and contract. Ship the additive schema change first, deploy code that works with both shapes, backfill, then drop the old shape in a later release. A release that needs a down migration to roll back is a release you cannot roll back fast.
7. Put new behavior behind a flag where you can. Default off in prod. Record the flag name, owner and removal date.
8. Write the rollback plan before deploying: the exact command, how long it takes, what data it cannot undo, and who decides. Example: `helm rollback api 41 -n prod`, `kubectl rollout undo deploy/api -n prod`, or redeploy the previous image digest.
9. Define the watch window and the signals: error rate, p99 latency, saturation, key business metric. Set the threshold that triggers rollback (for example, 5xx rate above 1 percent for 5 minutes).
10. Roll out in stages: canary (1 to 5 percent) or one region, wait, then 25, 50, 100. Use Argo Rollouts, Flagger, or the platform's traffic split.
11. Tag and sign: `git tag -s vX.Y.Z -m "vX.Y.Z"`, sign images with `cosign sign`, attach SBOM and checksums to the release.
12. After the watch window, close out: announce, remove dead flags on schedule, file follow-ups for anything that went sideways.

## Checklist

Version and notes:

- Version follows SemVer and matches across `package.json`, `pyproject.toml`, `Chart.yaml` (`version` and `appVersion`), and the git tag.
- `CHANGELOG.md` has the new section with date and compare link.
- Breaking changes have an upgrade note with before and after config.
- Deprecations list the version where removal happens.

Build and security:

- CI green on the tagged SHA, not only on the PR branch.
- `trivy image --severity HIGH,CRITICAL --exit-code 1` passes on the release image, or exceptions are recorded with expiry.
- `gitleaks detect --redact` clean on the release range.
- SBOM generated (`syft <image> -o spdx-json > sbom.spdx.json`) and attached.
- Image referenced by digest in the deploy manifest, not by a mutable tag.
- Artifacts signed (`cosign sign --yes <image>@sha256:...`), and `cosign verify` runs at deploy time or in admission.
- Lockfiles committed, no unreviewed dependency major bumps.

Data and config:

- Migrations are backward compatible with the currently running version.
- Long-running migrations tested against a prod-sized copy; lock time measured.
- Backup or snapshot taken and restore path known before destructive changes.
- New env vars and secrets exist in every target environment before deploy.
- Config defaults safe if the new variable is missing.

Flags and rollout:

- New behavior behind a flag (LaunchDarkly, Unleash, OpenFeature provider, or in-house), default off.
- Kill switch tested in staging.
- Canary or staged rollout configured with automatic abort on SLO breach (Argo Rollouts `AnalysisTemplate`, Flagger `metrics`).
- Deploy window avoids freeze periods and has people on hand.

Rollback:

- Rollback command written down and tried in staging.
- Rollback time known (target: under 10 minutes).
- Irreversible steps (data deletes, external API calls, emails sent) listed.
- Previous artifact still available (image not garbage collected, package not yanked).

Comms:

- Release owner and on-call named.
- Status page or customer note prepared if user-visible.
- Support team told about visible changes.

## Output format

```markdown
# Release vX.Y.Z: go/no-go

Owner: @name   On-call: @name   Window: YYYY-MM-DD HH:MM UTC
Risk: low | medium | high   (reason)

## Changes
- feat: ... (#123)
- fix: ... (#130)
- migration: add column orders.region (expand step)

## Gates
| Check | Status | Evidence |
|---|---|---|
| CI on tag SHA abc1234 | pass | link |
| Image scan | pass, 2 accepted lows | link |
| Migration dry run on staging copy | pass, 4s lock | link |

## Rollout
1. Canary 5% for 15 min. Abort if 5xx > 1% or p99 > 800ms.
2. 50% for 30 min.
3. 100%.

## Rollback
Command: kubectl argo rollouts undo api -n prod
Time: ~3 min. Not reversible: none (expand-only migration).
Decision: release owner or on-call, no approval needed.

## Blockers
| Severity | Item | Owner | Fix |
|---|---|---|---|

## Decision: GO | NO-GO
```

## Examples

Bad rollback plan:

```markdown
Rollback: revert the PR if something breaks.
```

Reverting a PR means a new build, a new pipeline run, and maybe 30 minutes. If the release dropped a column, the revert does not bring the data back.

Good rollback plan:

```markdown
Rollback: helm rollback payments 57 -n prod (previous release, image
sha256:3f1c...e9). Tested in staging on 2026-11-05, took 2m10s.
Migration 0042 only adds a nullable column, so the old code ignores it.
Flag `new-checkout` off first if the issue is in the new flow (instant).
Not reversible: confirmation emails already sent.
Trigger: 5xx > 1% or checkout success < 97% for 5 min.
```

Bad migration in a release:

```sql
ALTER TABLE orders RENAME COLUMN addr TO shipping_address;
```

Old pods still running during the rollout query `addr` and fail.

Good, split across releases:

```sql
-- vX.Y.0 (expand)
ALTER TABLE orders ADD COLUMN shipping_address text;
-- app writes both columns, reads new with fallback to old; backfill job runs
-- vX.Y+1.0 (contract), only after no running version reads addr
ALTER TABLE orders DROP COLUMN addr;
```

More rollout patterns and platform commands: [references/rollout-and-rollback.md](references/rollout-and-rollback.md).
