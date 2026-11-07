---
name: k8s-manifest-review
description: Review Kubernetes manifests, Kustomize overlays and rendered Helm output for pod security (securityContext, Pod Security Standards restricted profile), RBAC scope, NetworkPolicies, resource requests and limits, probes and image pinning, using kube-score, kubeconform, Checkov or Trivy, and return fixed YAML. Use when the user shares Deployment, StatefulSet, Pod, Role, ClusterRole or NetworkPolicy YAML, Kustomize overlays or the output of helm template, or opens a PR touching k8s/ or manifests/. For Helm chart structure, values defaults and templates use helm-review.
---

# Kubernetes Manifest Review

Check that workloads run with the least privilege the cluster allows, cannot talk to everything, cannot starve their neighbors, and can be rolled out and back safely. Render first, then review what the API server will actually receive.

## When to use

- The user shares raw manifests (`Deployment`, `StatefulSet`, `DaemonSet`, `Job`, `CronJob`, `Pod`, `Service`, `Ingress`).
- The user shares RBAC objects (`Role`, `ClusterRole`, `RoleBinding`, `ClusterRoleBinding`, `ServiceAccount`).
- The user shares a Kustomize overlay or rendered `helm template` output and asks if it is safe.
- A PR touches `k8s/`, `deploy/`, `manifests/` or `kustomization.yaml`.

Not for: Helm chart structure, `values.yaml` defaults, templates, dependencies and chart signing (use `helm-review`), the Dockerfile and image contents (use `container-security`), cluster creation in Terraform such as EKS or GKE settings (use `iac-review`), cloud IAM roles bound through IRSA or Workload Identity (use `cloud-iam-review`), or writing Kyverno and Gatekeeper admission policies (use `policy-as-code`).

## Steps

1. Render the final YAML. For Helm: `helm template rel ./chart -f values-prod.yaml > rendered.yaml`. For Kustomize: `kustomize build overlays/prod > rendered.yaml`. Review the rendered output, and trace fixes back to the template or values file.
2. Validate schemas: `kubeconform -strict -summary -kubernetes-version 1.30.0 rendered.yaml`. Deprecated APIs (`extensions/v1beta1`, `policy/v1beta1 PodSecurityPolicy`) are findings.
3. Run scanners where available:
   - `kube-score score rendered.yaml`
   - `checkov -f rendered.yaml --framework kubernetes`
   - `trivy config rendered.yaml`
   - `kubescape scan rendered.yaml` for NSA/CISA and MITRE mappings
4. Check every pod spec against the Pod Security Standards `restricted` profile (checklist below). Namespaces should carry `pod-security.kubernetes.io/enforce: restricted` unless a workload truly needs `baseline`.
5. Review RBAC. For each binding, write down who (subject), what (verbs and resources), and where (namespace or cluster). Flag wildcards, `secrets` read access, `pods/exec`, `escalate`, `bind`, `impersonate`, and anything bound to `system:authenticated` or `default` ServiceAccounts.
6. Review network reach. Is there a default-deny `NetworkPolicy` in the namespace? Does each workload have an explicit ingress and egress policy? Is egress to `169.254.169.254` blocked?
7. Review resources and health: requests and limits for CPU and memory, `livenessProbe`, `readinessProbe`, `PodDisruptionBudget` for replicated services, `replicas` above 1 for anything user-facing.
8. Check images and secrets: images pinned by digest or immutable tag, `imagePullPolicy` sensible, no secrets in `env.value` or ConfigMaps, `automountServiceAccountToken: false` where the pod does not call the API.
9. Write fixes as YAML patches against the source (template, values or base), then report.

## Checklist

Pod security (restricted profile):

- `securityContext.runAsNonRoot: true` and a numeric `runAsUser` above 10000.
- `allowPrivilegeEscalation: false` on every container.
- `capabilities.drop: ["ALL"]`; add back only what is needed (`NET_BIND_SERVICE`).
- `readOnlyRootFilesystem: true` with `emptyDir` mounts for writable paths.
- `seccompProfile.type: RuntimeDefault`.
- No `privileged: true`, `hostNetwork`, `hostPID`, `hostIPC`, `hostPath` volumes, or `hostPort`.
- `automountServiceAccountToken: false` unless the app talks to the API server.

RBAC:

- No `verbs: ["*"]` or `resources: ["*"]`. No `ClusterRole` where a namespaced `Role` works.
- `get`/`list`/`watch` on `secrets` only for workloads that need them, scoped with `resourceNames` where possible.
- No `create` on `pods/exec`, `pods/attach`, or `serviceaccounts/token` for app workloads.
- No `escalate`, `bind`, or `impersonate` verbs outside cluster admin tooling.
- One `ServiceAccount` per workload, not the namespace `default`.
- Audit with `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>` or `rbac-tool who-can`.

Network:

- Default deny for ingress and egress per namespace.
- Explicit allow rules using `podSelector` and `namespaceSelector`, not `ipBlock: 0.0.0.0/0`.
- Egress to DNS (`kube-dns` on UDP and TCP 53) allowed explicitly when egress is denied by default.
- Cloud metadata endpoint blocked unless the workload uses node credentials on purpose.

Resources and reliability:

- `resources.requests` set for CPU and memory; `limits.memory` set. CPU limits optional, depending on team policy.
- `readinessProbe` and `livenessProbe` defined; liveness does not hit a dependency like the database.
- `PodDisruptionBudget` with `minAvailable` or `maxUnavailable` for services with more than one replica.
- `topologySpreadConstraints` or anti-affinity for multi-replica services.

Images and config:

- `image: registry.example.com/app@sha256:<digest>` or an immutable tag, never `:latest`.
- Secrets mounted from `Secret` objects, External Secrets Operator, or the Secrets Store CSI driver. No plaintext values in `env`.
- Ingress has TLS configured and no wildcard host unless intended.

See the Kubernetes docs page "Pod Security Standards" for the full field list for each profile.

## Output format

| Severity | File | Line | Kind/Name | Issue | Fix |
|---|---|---|---|---|---|
| Critical | k8s/rbac.yaml | 8 | ClusterRole/app | `resources: ["*"]`, `verbs: ["*"]` bound to app SA | Namespaced Role with `get` on `configmaps` only |
| High | charts/api/templates/deployment.yaml | 22 | Deployment/api | No `securityContext`, runs as root | Add restricted securityContext (see patch) |
| Medium | k8s/deploy.yaml | 31 | Deployment/api | No memory limit | `resources.limits.memory: 512Mi` |

After the table:

1. YAML patches or full corrected manifests for Critical and High.
2. Scanner summary (tool, version, counts) and any false positives with reasons.
3. Cluster-level gaps you noticed but could not fix in the manifest (missing PSA labels, no CNI support for NetworkPolicy).

Severity: Critical (container escape path, cluster-wide write RBAC, secrets readable cluster-wide), High (root or privileged pod, no NetworkPolicy on an internet-facing service, `pods/exec` granted), Medium (missing limits or probes, unpinned image), Low (labels, annotations, hygiene).

## Examples

Bad: root, writable filesystem, no limits, latest tag, token mounted, secret inline.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          image: registry.example.com/api:latest
          env:
            - name: DB_PASSWORD
              value: "example-password-not-real"
```

Good: restricted security context, pinned image, limits, probes, secret reference.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  selector:
    matchLabels: { app: api }
  template:
    metadata:
      labels: { app: api }
    spec:
      serviceAccountName: api
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: api
          image: registry.example.com/api@sha256:<digest>
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests: { cpu: 100m, memory: 256Mi }
            limits: { memory: 512Mi }
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef: { name: api-db, key: password }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - { name: tmp, emptyDir: {} }
```

Default-deny NetworkPolicy to pair with it:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```
