---
name: incident-postmortem
description: Write a blameless postmortem from incident notes, chat logs, alerts and deploy history, with a UTC timeline, impact numbers, root cause and contributing factors, and owned, dated action items. Use after an outage or security incident is resolved, when the user shares incident notes or a Slack export and asks for a postmortem, incident review, RCA or retro document.
---

# Incident Postmortem

Turn a messy pile of chat logs, graphs and memory into a document that explains what happened, why the system allowed it, and what will change. Blame the system and the process, never a person.

## When to use

- An incident is resolved and the team needs a written review.
- The user pastes a Slack or Teams export, an incident timeline, alert history or deploy logs and asks for a postmortem or RCA.
- A draft postmortem exists and needs review for blame, missing impact data, or vague action items.
- A security incident needs an internal review (separate from any legal or regulatory notice).

Not for: handling the incident while it is still live (use `incident-response`), or debugging a bug in code with no incident attached (use `debugging-playbook`).

## Steps

1. Gather sources: incident channel export, alert history (PagerDuty, Opsgenie), deploy and flag audit logs, dashboard screenshots with time ranges, the status page history, support ticket counts. Ask for what is missing instead of inventing it.
2. Build the timeline in UTC. One line per event: time, what happened, source. Include the start of impact (often earlier than detection), detection, declaration, each mitigation attempt, mitigation, and resolution.
3. Compute the key durations: time to detect (impact start to alert), time to mitigate (alert to user impact ending), total duration. These are what action items should shrink.
4. Quantify impact with numbers: requests failed, users or tenants affected, revenue or SLO budget consumed, data affected. If a number is an estimate, say how it was estimated.
5. Find the root cause and contributing factors. Ask "why" until you reach something the team can change in the system or process. Usually there is more than one factor: the triggering change, the missing safeguard, and the gap that slowed detection or recovery.
6. Rewrite every sentence that names a person as the cause. "Alice ran the wrong migration" becomes "The migration ran against prod because the CLI defaulted to the prod context and nothing asked for confirmation."
7. List what went well. Real things: the alert fired in 2 minutes, rollback worked first try. This tells the team what not to break.
8. Write action items. Each has an owner (a person, not a team), a due date, a ticket link, and a type: prevent, detect, or mitigate. Prefer changes to systems (guardrails, automation, alerts) over "be more careful" or "add to docs".
9. Mark the security angle if there is one: exposed data, credentials rotated, regulator or customer notices sent, and who signed off.
10. Review the draft for blame language, missing numbers, and action items that are not testable. Schedule the review meeting within 5 business days of the incident.

## Checklist

Facts:

- All times in UTC with the date.
- Impact start, detection, mitigation and resolution times all present.
- Time to detect and time to mitigate computed.
- Impact in numbers with the source query or dashboard link.
- Triggering change identified with a link (PR, deploy ID, flag change), or stated as unknown.

Blameless:

- No person named as a cause. Names appear only in roles (IC, responder) or as action item owners.
- No "should have", "failed to", "human error", "carelessness". Replace with the condition that made the action possible.
- Decisions explained with the information available at the time, not with hindsight.

Root cause:

- At least one contributing factor beyond the trigger (missing test, missing alert, unsafe default, unclear runbook).
- "Why did detection take N minutes" answered.
- "Why did mitigation take N minutes" answered.
- Five whys stop at something the team can change, not at "the network is unreliable".

Action items:

- Every item has owner, due date, ticket, and type (prevent, detect, mitigate).
- Items are specific and testable: "Add `lock_timeout = 5s` to migration runner" not "improve migrations".
- At least one item addresses detection time if it was over 5 minutes.
- No more than about 10 items; the rest go in a backlog note. Long lists do not get done.
- Follow-up date set to check completion.

Security incidents:

- Data types and record counts exposed, or "none, confirmed by <method>".
- Credentials rotated, with times.
- Notices sent (customers, regulator under GDPR Art. 33, card brands under PCI DSS 12.10) and who approved them.
- Evidence location recorded.

## Output format

```markdown
# Postmortem: <short title>

Date: YYYY-MM-DD   Severity: SEV<N>   Status: draft | reviewed
Authors: <names>   IC: <name>   Review meeting: YYYY-MM-DD

## Summary
Two to four sentences: what broke, who was affected, for how long, how it was fixed.

## Impact
| Metric | Value | Source |
|---|---|---|
| Duration of user impact | 47 min (14:02 to 14:49 UTC) | API dashboard |
| Failed requests | ~182,000 (31% of checkout calls) | Prometheus query link |
| Customers affected | ~4,100 | Support + logs |
| SLO budget used | 68% of 28-day budget | SLO dashboard |

Time to detect: 7 min   Time to mitigate: 40 min

## Timeline (UTC)
| Time | Event | Source |
|---|---|---|
| 13:58 | Deploy api v2.14.0 starts | Argo CD |
| 14:02 | 5xx rate rises on /checkout | Grafana |
| 14:09 | ApiErrorBudgetFastBurn pages on-call | PagerDuty |

## Root cause and contributing factors
- Trigger: ...
- Why it reached prod: ...
- Why detection took 7 min: ...
- Why mitigation took 40 min: ...

## What went well
- ...

## What was hard
- ...

## Action items
| # | Action | Type | Owner | Due | Ticket |
|---|---|---|---|---|---|
| 1 | Run migrations with lock_timeout=5s in the deploy job | prevent | @name | YYYY-MM-DD | OPS-123 |

## Appendix
Links to channel export, dashboards, PRs.
```

When reviewing an existing draft, return findings:

| Severity | Section | Line | Issue | Fix |
|---|---|---|---|---|
| high | Root cause | 22 | "Bob forgot to run the tests" blames a person | "The merge was allowed without the test job passing; branch protection did not require it" |

## Examples

Bad root cause:

```markdown
Root cause: Human error. The engineer deployed a bad config. We will
remind everyone to double check configs before deploying.
```

It names no system fix, blames a person, and the action item cannot be tested.

Good:

```markdown
Root cause: A config change set `DB_POOL_MAX=5` (was 50) in the prod
values file. The value was meant for staging; both files share a
template and the diff in review showed only the template.

Contributing factors:
- Helm values are not validated against a schema, so no lower bound
  was enforced.
- No alert on DB pool saturation; the first signal was user-facing
  5xx, 7 minutes after deploy.
- Rollback needed a full pipeline run (18 min) because the deploy job
  has no "redeploy previous" path.

Action items:
1. Add values.schema.json with minimum 20 for DB_POOL_MAX (prevent, @dev-a, 2026-11-21, OPS-411)
2. Alert when pool wait time p95 > 100ms for 2 min (detect, @dev-b, 2026-11-14, OPS-412)
3. Add `helm rollback` job to the pipeline, target under 3 min (mitigate, @dev-c, 2026-11-28, OPS-413)
```

Bad action item list:

```markdown
- Improve monitoring
- Be more careful with deploys
- Update docs
```

Good: each item names a specific change, an owner, a date and the metric it should move, as in the list above.
