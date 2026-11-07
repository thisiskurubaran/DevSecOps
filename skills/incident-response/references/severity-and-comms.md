# Severity levels and comms templates

Adjust the thresholds to your product. The point is that everyone uses the same words.

## Severity

| Level | Meaning | Examples | Response |
|---|---|---|---|
| SEV1 | Critical user impact or confirmed data exposure | Full outage, payments failing, customer data leaked, active attacker | Page now, IC required, exec and legal informed, updates every 30 min |
| SEV2 | Major degradation for many users, or a contained security issue | One region down, error rate over 5 percent, leaked key with no misuse found yet | Page now, IC required, updates every 60 min |
| SEV3 | Minor impact or a workaround exists | One feature broken, slow for a subset, internal tool down | On-call handles in hours, no page outside business hours |
| SEV4 | No user impact yet | Redundancy lost, cert expiring in 7 days, noisy alert | Ticket |

Security incidents start at SEV2 or higher until scope is known.

## Roles

| Role | Does | Does not |
|---|---|---|
| Incident Commander | Sets priorities, assigns work, decides on rollback, calls escalation | Debug or type commands |
| Ops lead | Investigates, runs mitigations, reports findings to IC | Make customer statements |
| Comms lead | Status page, stakeholder updates, support team briefings | Speculate on cause |
| Scribe | Keeps the timeline with UTC times, links, commands run | Filter what goes in |

## Status page templates

Investigating:

```
We are investigating elevated errors on <feature> starting at HH:MM UTC.
Some users may see <symptom>. Next update by HH:MM UTC.
```

Identified / mitigating:

```
We have identified the cause of <symptom> and are rolling out a fix.
Affected: <scope>. Next update by HH:MM UTC.
```

Resolved:

```
<Feature> has been working normally since HH:MM UTC. Between HH:MM and
HH:MM UTC, <scope> saw <symptom>. We will publish a summary within
<N> business days.
```

Do not name vendors, people or internal systems in public updates. Do not guess at cause in the first update.

## Internal update template

```
SEV<N> <name> | <status> | HH:MM UTC
Impact: <users, scope, trend: growing / stable / shrinking>
Since last update: <what changed>
Next steps: <action, owner, ETA>
Need: <help or decisions needed, or "nothing">
Next update: HH:MM UTC
```

## Escalation triggers

- No mitigation path after 30 minutes on SEV1, 60 on SEV2.
- Impact is growing.
- Personal data, payment data or credentials may be exposed: page security, inform legal and privacy. GDPR Article 33 requires notifying the supervisory authority within 72 hours of becoming aware of a personal data breach; PCI DSS 12.10 requires an incident response plan with card brand notification.
- The fix needs another team, a vendor, or the cloud provider (open a support case at the highest severity your plan allows).

## Evidence to keep for security incidents

| Source | How |
|---|---|
| Cloud audit logs | Export CloudTrail / Azure Activity Log / GCP Audit Logs for the window to a locked bucket |
| Host disk | `aws ec2 create-snapshot --volume-id vol-EXAMPLE --description "inc-YYYYMMDD"` |
| Container | `kubectl logs <pod> --previous`, `kubectl get pod <pod> -o yaml`, copy files out before deletion |
| Memory | LiME or AVML on Linux, before shutdown, if the team has the skill |
| App logs | Export from the log backend; extend retention on the affected index |
| Git | Record the commit, push event and actor from the provider audit log |

Write down the hash of each evidence file (`sha256sum`) and who collected it.
