# MITRE mapping, triage hints and Tetragon policies

## MITRE ATT&CK for Containers

| Behavior | Technique | Typical Falco signal |
|---|---|---|
| `kubectl exec` or shell in a container | T1609 Container Administration Command, T1059.004 Unix Shell | Terminal shell in container, K8s audit exec |
| New pod or privileged pod created by an unusual user | T1610 Deploy Container | K8s audit create on `pods` |
| Container escape attempt (mount host fs, `nsenter`, write to `/proc/sys`) | T1611 Escape to Host | Mount or `setns` from a container |
| Listing pods, secrets, nodes from inside a pod | T1613 Container and Resource Discovery | `kubectl` or `curl` to the API server from a workload |
| Crypto miner | T1496 Resource Hijacking | Miner process names, mining pool ports |
| Reading credentials from files or SA tokens | T1552.001 Credentials In Files | Sensitive file read |
| setuid binary abuse, kernel exploit | T1068 Exploitation for Privilege Escalation | setuid, `capset`, unexpected root process |
| New ClusterRoleBinding to `cluster-admin` | T1098 Account Manipulation | K8s audit create on `clusterrolebindings` |
| Using a stolen service account token | T1078.001 Valid Accounts: Default Accounts | Audit events from an SA outside its namespace |

Check technique IDs against attack.mitre.org when you write them into tags; the matrix gets revised.

## Triage hints

Shell in container:
- Expected: a named engineer ran `kubectl exec` during a ticketed debug session, and the audit log shows the same user.
- Suspicious: no matching audit event, parent is the app process (`java > sh`, `node > sh`), or the shell runs `curl`, `wget`, `base64`.
- An app process spawning a shell usually means command injection or RCE. Treat as malicious until shown otherwise.

Unexpected outbound connection:
- Compare `fd.sip` and `fd.sport` with what the service is meant to call. Workloads that only serve traffic should not open new outbound connections.
- Raw IPs on high ports, Tor ports, or mining pool ports (3333, 4444, 5555, 14444) are strong signals.

Write below /etc or binary dirs:
- Package managers (`apt`, `apk`, `yum`, `pip`) in a running container are drift. Either the image is wrong or someone is installing tools.
- An app writing to `/etc/ld.so.preload` or `/etc/cron*` is persistence. Escalate.

Sensitive file read:
- `/var/run/secrets/kubernetes.io/serviceaccount/token` read by anything other than the app or its SDK is a credential theft signal. Rotate by deleting the pod after evidence is preserved, and review audit logs for that SA.

K8s audit events (fields `ka.verb`, `ka.user.name`, `ka.target.resource`, `ka.target.subresource`, `ka.target.namespace`):
- `exec` subresource on `pods` outside a change window or by a user who is not on-call.
- `create` on `clusterrolebindings` referencing `cluster-admin` by anyone but your GitOps controller.
- `list` or `get` on `secrets` across namespaces by a human or an app SA.

## Tetragon

Observe file writes below `/etc` in containers. No action, events only.

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: watch-etc-writes
spec:
  kprobes:
    - call: "security_file_permission"
      syscall: false
      args:
        - index: 0
          type: "file"
        - index: 1
          type: "int"
      selectors:
        - matchArgs:
            - index: 0
              operator: "Prefix"
              values:
                - "/etc/"
            - index: 1
              operator: "Equal"
              values:
                - "2"   # MAY_WRITE
```

Read the events with `tetra getevents -o compact`, or from the Tetragon pod logs if they go to your SIEM.

Only after a clean observation period, add enforcement to that selector, scoped to one namespace with `TracingPolicyNamespaced` or a `podSelector`:

```yaml
          matchActions:
            - action: Sigkill
```

Cautions:
- `Sigkill` kills the process that made the call. If that process is PID 1, the container restarts, and a crash loop is now your outage.
- `Override` changes a function's return value and needs kernel support for error injection (`CONFIG_BPF_KPROBE_OVERRIDE`) on the hooked function. Test on the same kernel as production.
- Roll out enforcement to one namespace first, with an owner watching.
