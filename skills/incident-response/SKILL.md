---
name: incident-response
description: Guide a live incident or write a runbook for one, covering severity triage, roles, containment, evidence preservation, status updates and escalation for outages and security incidents such as leaked credentials or compromised hosts. Use when production is down or degraded, a breach or leaked secret is suspected, the user asks "what do we do now", or wants an incident runbook or on-call playbook written.
---

# Incident Response

Get from "something is wrong" to "users are fine and we know what happened" with clear roles, fast containment, and a record good enough to write the postmortem from.

## When to use

- Production is down, slow, or returning wrong data, and the user needs to act now.
- A secret, key or token was pushed to a public repo or shows up in logs.
- A host, container, account or CI runner may be compromised.
- The user wants a runbook for a known failure mode, or an on-call playbook for a team.

Not for: writing the postmortem after the incident is resolved (use `incident-postmortem`), planning credential rotation as routine work (use `secrets-management`), or setting up alerts and dashboards (use `observability-setup`).

## Steps

During a live incident, keep answers short and ordered. Do the next useful thing, not the full list.

1. Declare and assign severity. Use the table in [references/severity-and-comms.md](references/severity-and-comms.md). When unsure, pick the higher one; downgrading is cheap.
2. Assign roles: Incident Commander (decides, coordinates, does not debug), Ops lead (hands on keyboard), Comms lead (status page, stakeholders), Scribe (timeline). One person can hold several roles in a small team, but the IC role is explicit.
3. Open a channel (`#inc-YYYYMMDD-short-name`) and a timeline doc. Log every action with a UTC timestamp from here on.
4. Assess impact: who is affected, since when, what percentage of requests, which regions or tenants. Pull from dashboards, not guesses.
5. Look for the recent change. `kubectl rollout history`, deploy log, feature flag audit log, `git log --since="2 hours ago"` on infra repos, cloud provider status page. Most incidents follow a change.
6. Mitigate before you diagnose. Options in order of speed: flip the flag off, roll back the deploy, shift traffic away from the bad region, scale up, rate limit or shed load, disable the failing feature. Root cause can wait.
7. For security incidents, contain while preserving evidence:
   - Leaked credential: revoke or rotate first, then check usage logs (CloudTrail, audit logs) for the window it was exposed. Removing it from git history does not un-leak it.
   - Compromised host or pod: isolate the network (security group, NetworkPolicy deny-all), snapshot the disk and capture memory if possible, then replace. Do not just delete it.
   - Compromised account: disable sessions, reset credentials and MFA, review recent actions.
8. Communicate on a fixed cadence: internal update every 30 minutes for SEV1, external status page update within 15 minutes of declaring for customer-visible impact. Say what is known, what is being done, and when the next update comes.
9. Escalate when: no mitigation path after 30 minutes, impact grows, data loss or exposure is possible, or the fix needs a team that is not in the room. Security incidents with personal data go to legal and privacy right away (GDPR breach notice is 72 hours from awareness).
10. Confirm resolution with the same metrics that showed the problem. Watch for at least one full traffic cycle before closing.
11. Hand off: close the incident, keep the timeline, open the postmortem doc with an owner and a date. Use `incident-postmortem`.

## Checklist

Setup (before any incident):

- Severity levels defined and posted where on-call can see them.
- Paging works: PagerDuty, Opsgenie, or Grafana OnCall schedule with a secondary.
- Runbook linked from every alert (`runbook_url` annotation).
- Break-glass access documented, tested, and audited.
- Status page access for at least two people per shift.
- Contacts for cloud provider support, legal, privacy, and PR in the runbook.

During:

- IC named in the channel topic.
- Timeline started with UTC timestamps.
- Impact stated in user terms ("EU customers cannot log in"), not system terms.
- Mitigation attempted before deep debugging.
- Every production change during the incident announced in the channel before it runs.
- Evidence preserved for security incidents: logs exported, disk snapshot (`aws ec2 create-snapshot`), `kubectl logs --previous`, cloud audit logs retained.
- Status page updated; next update time stated.

Leaked secret, specific:

- Credential revoked or rotated (AWS: `aws iam update-access-key --status Inactive`, then delete; GitHub: revoke PAT; Stripe/Slack: roll in the dashboard).
- Usage checked for the exposure window (CloudTrail `LookupEvents` by `AccessKeyId`).
- Secret removed from the repo and history rewritten with `git filter-repo` only after rotation, and forks/caches considered still exposed.
- `gitleaks detect` run on the repo to find others.

Close:

- Metrics back to baseline for a full cycle.
- Temporary mitigations listed with owners (flags left off, rate limits added, capacity raised).
- Postmortem owner and due date set.

## Output format

Live incident, post this in the channel and keep it updated:

```markdown
**INCIDENT: <short name>**  SEV<1-4>  Status: investigating | mitigated | resolved
IC: @name  Ops: @name  Comms: @name  Scribe: @name
Started: 2026-11-07 14:02 UTC  Detected: 14:09 UTC (alert ApiErrorBudgetFastBurn)

Impact: <who, what, how many>
Current theory: <one line>
Doing now: <action, owner>
Next update: 14:45 UTC

Timeline:
- 14:09 alert fired
- 14:12 IC declared SEV2
- 14:18 rolled back api to rev 41
```

Runbook request, use this template:

```markdown
# Runbook: <alert or failure mode>
Severity guide: <when SEV1 vs SEV2>
Signals: <dashboard link, queries>
Quick checks: <3 to 5 commands with expected output>
Mitigations: <ordered, with commands and side effects>
Escalation: <team, pager, when>
Do not: <known traps>
```

## Examples

Bad first response to "API 500s spiked after deploy":

```markdown
Let's look at the logs and figure out the root cause. Check the stack
traces and see which function is failing, then we can write a fix.
```

That leaves users broken while someone reads stack traces.

Good:

```markdown
1. Declare SEV2, you are IC unless someone else takes it.
2. Roll back now: kubectl rollout undo deploy/api -n prod
   (or helm rollback api <prev> -n prod). Announce it in the channel first.
3. Watch 5xx rate on the API dashboard for 5 minutes.
4. If it drops: mitigated. Post a status update, then look at the diff.
   If not: the deploy was not the cause. Check DB and upstream status next.
```

Bad response to a leaked AWS key in a public repo:

```sh
git rm config/aws.env && git commit -m "remove key" && git push
```

The key is still in history, forks and scraper caches. Bots find keys in public repos within minutes.

Good:

```sh
# 1. Kill the key first
aws iam update-access-key --user-name ci-deploy --access-key-id AKIAEXAMPLEEXAMPLE00 --status Inactive
# 2. Check what it did
aws cloudtrail lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAEXAMPLEEXAMPLE00 \
  --start-time 2026-11-07T10:00:00Z --max-results 50
# 3. Issue a new key via your secret store, update consumers, delete the old key
aws iam delete-access-key --user-name ci-deploy --access-key-id AKIAEXAMPLEEXAMPLE00
# 4. Then clean history and look for more
git filter-repo --path config/aws.env --invert-paths
gitleaks detect -v
```

Look for new IAM users, access keys, EC2 instances in unused regions, or Lambda functions created in the exposure window.
