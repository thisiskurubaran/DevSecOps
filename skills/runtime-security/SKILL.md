---
name: runtime-security
description: Detect and respond to threats in running containers and Kubernetes workloads by writing and tuning Falco rules and Tetragon TracingPolicies, triaging runtime alerts (shell in container, unexpected outbound connections, writes below /etc, sensitive file reads, privilege escalation, crypto miners, exec into pod, new ClusterRoleBindings), cutting noise without losing detection, mapping to MITRE ATT&CK for Containers, and routing alerts with Falcosidekick. Use when the user shares Falco or Tetragon rules, pastes a runtime alert or K8s audit event, asks why a detection is noisy or silent, or wants runtime detection set up for a cluster.
---

# Runtime Security

Manifests and images get checked before deploy. This skill covers what happens after: a process does something it should not, and you need a rule that catches it, an alert someone trusts, and a clear call on whether it is an incident.

## When to use

- The user shares a Falco rules file, a `falco_rules.local.yaml` override, or a Tetragon `TracingPolicy`.
- The user pastes a Falco alert, Tetragon event, or Kubernetes audit log entry and asks "is this bad?"
- A detection is too noisy ("Terminal shell in container fires 400 times a day") or never fires.
- Someone wants runtime detection set up for a cluster, or alerts routed to Slack or a SIEM.
- The user asks how to block a behavior at runtime, not just alert on it.

Not for: pre-deploy checks on pod specs, RBAC or NetworkPolicies (use `k8s-manifest-review`), Dockerfile hardening or image scan results (use `container-security`), handling an incident that is already confirmed (use `incident-response`), or general logs, metrics and SLO alerting (use `observability-setup`).

## Steps

1. Find out what is deployed. Falco version and driver (`modern_ebpf` is the default on recent releases), which rule files are loaded (`falco_rules.yaml`, `falco-incubating_rules.yaml`, local overrides), whether the `k8saudit` plugin is on, and whether Tetragon runs alongside. Rule behavior differs between versions, so do not guess.
2. For a rule review, validate first: `falco -V /etc/falco/falco_rules.local.yaml`. Then read each rule for scope, condition cost, output fields and priority (see checklist).
3. Never edit the upstream rule files. Put changes in a local file loaded after them, and use `override` to append or replace:
   - `override: { condition: append }` to add `and not ...` to an upstream rule.
   - `override: { exceptions: append }` to add exception values.
   - `override: { enabled: replace }` with `enabled: false` to turn a rule off, with a comment saying why.
4. Manage rule artifacts with falcoctl, not by copying YAML around: `falcoctl artifact install falco-rules:3`, and `falcoctl artifact follow` in the cluster to pick up updates. Pin a major version so a rules release cannot change behavior under you.
5. For alert triage, collect the context before deciding: full output fields, container image and tag, namespace, pod owner (Deployment, Job, CronJob), parent process chain (`proc.pname`, `proc.aname[2]`), user, and the time window. Then check if the same image does this in other pods or other clusters.
6. Classify each alert: expected (known tooling, document it and tune), suspicious (unexplained, needs an owner to confirm), or malicious (matches attacker behavior or has no legitimate explanation). Use the triage hints below.
7. Tune noise with the narrowest exception that still holds. Scope by image repository plus process plus namespace, not by process name alone. Prefer `exceptions` over appending to `condition` because they are easier to read and audit. Every exception gets a comment with the owner and reason.
8. Before turning off a rule, check what else would catch the same technique. If nothing would, keep it at a lower priority instead of disabling it.
9. Enforcement with Tetragon: start every policy without a `matchActions` block (observe only), run it for at least a week, review `tetra getevents -o compact`, then add `Sigkill` or `Override`. Scope with `podSelector` or `TracingPolicyNamespaced`. A wrong kill rule on a hot path takes production down.
10. Map each rule and alert to MITRE ATT&CK for Containers using [references/mitre-and-triage.md](references/mitre-and-triage.md), and add the IDs to `tags`.
11. Route alerts by priority with Falcosidekick: `Critical` and above to the pager or Slack channel, everything to the SIEM. Set `json_output: true` and `http_output` in `falco.yaml` pointing at Falcosidekick.
12. Hand off to `incident-response` when an alert is classified malicious, when a shell, miner or escape attempt has no owner after a short check, or when a secret or service account token may have been read. Preserve the pod first (cordon the node, apply a deny-all NetworkPolicy, do not delete the pod).

## Checklist

Rule quality:

- Condition starts with a cheap filter (`evt.type`, a macro like `spawned_process` or `open_write`) before string matching.
- Scoped to containers with the `container` macro unless host activity is the point.
- Lists and macros used for repeated values, named for intent (`allowed_backup_images`, not `list1`).
- Output includes enough to triage without a second lookup: `%proc.cmdline`, `%proc.pname`, `%user.name`, `%container.id`, `%container.image.repository`, `%k8s.ns.name`, `%k8s.pod.name`, plus `%fd.name` or `%fd.sip`/`%fd.sport` for file and network rules.
- Priority matches impact: `CRITICAL` for likely compromise (miner, escape, shadow file read), `WARNING` for suspicious, `NOTICE` or lower for audit trail.
- `tags` include the MITRE technique and a category (`container`, `network`, `filesystem`).
- Exceptions use `fields` and `comps` scoped by image and process, each with an owner comment.

Detection coverage (minimum set):

- Shell spawned in a container with a TTY (`Terminal shell in container`).
- Write below `/etc`, `/usr/bin`, `/usr/sbin`, or `/bin` inside a container.
- Read of `/etc/shadow`, `/root/.ssh/`, or service account tokens by unexpected processes.
- Outbound connection from a workload that should only receive traffic.
- Package manager run in a running container (drift).
- `setuid` binary run or `capset` from a non-root process.
- Known miner process names or connections to mining pool ports.
- K8s audit: `exec` or `attach` into a pod, new `ClusterRoleBinding` to `cluster-admin`, privileged pod created, secret listed by an unusual user.

Hardening that makes detection cheaper (flag if missing, fix belongs to `k8s-manifest-review`):

- `seccompProfile: { type: RuntimeDefault }` on every pod.
- AppArmor profile set (`runtime/default` or a custom one).
- `readOnlyRootFilesystem: true` so drift writes fail instead of only alerting.
- No shells or package managers in the image, which makes shell alerts rare and meaningful.

## Output format

For alert triage:

| Time (UTC) | Rule | Priority | Namespace / Pod | Image | Process chain | MITRE | Verdict | Next step |
|---|---|---|---|---|---|---|---|---|
| 2026-11-02 14:03 | Terminal shell in container | NOTICE | payments / api-7f9c | registry.example.com/payments-api:1.4.2 | containerd-shim > bash | T1609 | Suspicious | Ask payments on-call who ran `kubectl exec`; check audit log |
| 2026-11-02 14:05 | Detect outbound connections to common miner pool ports | CRITICAL | payments / api-7f9c | registry.example.com/payments-api:1.4.2 | bash > xmrig | T1496 | Malicious | Isolate pod, hand off to `incident-response` |

For a rule review:

| Severity | File | Rule | Issue | Fix |
|---|---|---|---|---|
| High | falco_rules.local.yaml | Allow debug shells | Exception on `proc.name = bash` alone silences shell detection in every container | Scope the exception to the debug image and namespace |
| Medium | falco_rules.local.yaml | Write below etc | Output has no `%container.image.repository` | Add image and pod fields |

After the table: the fixed rule YAML, a list of exceptions added with owners, what coverage was lost (if any), and any alert you could not classify without more context.

## Examples

Bad: blinds shell detection everywhere, no scope, output useless for triage.

```yaml
- rule: Terminal shell in container
  condition: spawned_process and shell_procs and not proc.name in (bash, sh)
  output: shell
  priority: DEBUG
```

Good: upstream rule untouched, narrow exception with an owner, in a local override file.

```yaml
# falco_rules.local.yaml, loaded after falco_rules.yaml
# Owner: platform team. The toolbox image is our approved debug pod.
- rule: Terminal shell in container
  exceptions:
    - name: approved_debug_toolbox
      fields: [k8s.ns.name, container.image.repository]
      comps: [=, =]
      values:
        - [debug, registry.example.com/platform/toolbox]
  override:
    exceptions: append
```

Good: a custom rule with a cheap filter, useful output and MITRE tags.

```yaml
- list: sensitive_paths
  items: [/etc/shadow, /etc/sudoers]

- rule: Sensitive file read in container
  desc: A container process opened a credential file for reading
  condition: >
    open_read and container
    and fd.name in (sensitive_paths)
    and not proc.name in (sshd, sudo)
  output: >
    Sensitive file read (file=%fd.name proc=%proc.cmdline parent=%proc.pname
    user=%user.name container=%container.id image=%container.image.repository
    ns=%k8s.ns.name pod=%k8s.pod.name)
  priority: CRITICAL
  tags: [container, filesystem, mitre_credential_access, T1552.001]
```

Tetragon policies and the alert triage guide are in [references/mitre-and-triage.md](references/mitre-and-triage.md).
