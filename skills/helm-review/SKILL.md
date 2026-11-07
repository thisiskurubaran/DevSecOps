---
name: helm-review
description: Review Helm charts for insecure values.yaml defaults, template bugs (unquoted values, tpl on user input, lookup misuse, secrets in ConfigMaps or NOTES.txt, missing values.schema.json), dependency pinning in Chart.yaml and Chart.lock, chart signing and provenance, and secrets handling, by rendering with helm template and scanning with kubeconform, kube-score, Checkov, Trivy, kube-linter or Polaris. Use when the user shares a chart directory, Chart.yaml, values.yaml or templates/*.yaml, asks if a chart is safe to install or publish, or opens a PR touching charts/.
---

# Helm Chart Review

A chart is code that writes manifests. Review the defaults a user gets with no overrides, the templates that turn values into YAML, and the supply chain around the chart. Then render it and scan what comes out.

## When to use

- The user shares a chart directory, `Chart.yaml`, `Chart.lock`, `values.yaml` or files under `templates/`.
- The user asks if a third-party chart is safe to install, or if their own chart is ready to publish.
- A PR touches `charts/`, `helm/`, `Chart.yaml`, `values*.yaml` or `values.schema.json`.
- `helm lint`, `ct lint` or a scanner run on a chart produced findings the user wants triaged.

Not for: plain manifests or Kustomize overlays with no chart (use `k8s-manifest-review`), Dockerfiles and image scan results (use `container-security`), signing keys, keyless signing and attestations in depth (use `artifact-signing`), secret rotation and vault design (use `secrets-management`).

## Steps

1. Lint first: `helm lint ./chart --strict` and again with each real values file, `helm lint ./chart --strict -f values-prod.yaml`. If the repo uses chart-testing, run `ct lint --config ct.yaml --target-branch main`.
2. Read `values.yaml` as the default install. Anything insecure here ships to every user who does not override it. Check the values checklist below.
3. Read the templates. Look for unquoted strings, `tpl` on values a chart user controls, `lookup` used as if it always returns data, and secret values rendered into ConfigMaps, annotations or `NOTES.txt`.
4. Check for `values.schema.json`. Without one, a typo like `securityContex:` is silently ignored and the pod runs with defaults. `helm lint` and `helm install` validate against the schema when it exists.
5. Render with defaults and with production values:
   - `helm template rel ./chart > rendered-default.yaml`
   - `helm template rel ./chart -f values-prod.yaml > rendered-prod.yaml`
   - Use `--show-only templates/configmap.yaml` to inspect one file.
6. Scan the rendered output (see [references/scanners.md](references/scanners.md) for commands and what each catches):
   - `kubeconform -strict -summary -kubernetes-version 1.30.0 rendered-prod.yaml`
   - `kube-score score rendered-prod.yaml`
   - `checkov -d ./chart --framework helm`
   - `trivy config ./chart`
   - `kube-linter lint ./chart`
   - `polaris audit --audit-path rendered-prod.yaml --format pretty`
7. Check dependencies: every entry in `Chart.yaml` `dependencies` has an exact or tightly bounded `version`, `Chart.lock` is committed and matches (`helm dependency build` fails if it is out of date), and repositories use `https://` or `oci://`.
8. Check provenance: is the chart signed (`helm package --sign`) with a `.prov` file, or pushed to an OCI registry and signed with cosign? Does the install path verify it (`helm install --verify`, `helm verify`, `cosign verify`)?
9. Check secrets handling: no real secrets in any `values*.yaml` in git. Expect helm-secrets with SOPS, External Secrets Operator, or Sealed Secrets.
10. Trace every finding back to a values default or a template line, write the fix there, and report.

## Checklist

values.yaml defaults:

- `podSecurityContext.runAsNonRoot: true`, numeric `runAsUser`, `seccompProfile.type: RuntimeDefault`.
- `securityContext.allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`.
- `privileged`, `hostNetwork`, `hostPID` and `hostPath` default to off. If the chart exposes them, the default is `false` or empty.
- `resources` has requests and a memory limit by default, not `{}` with a comment telling users to fill it in.
- `image.tag` is not `latest` and does not fall back to `latest`. Support `image.digest` and prefer it over the tag when set.
- `serviceAccount.automount: false` (or `automountServiceAccountToken: false`) unless the app calls the API server.
- `serviceAccount.create: true` with a chart-specific name, not the namespace `default`.
- `rbac.create` grants only what the app needs. No wildcard verbs or resources in the default Role.
- `ingress.enabled: false` by default; when enabled, TLS is configurable.
- `networkPolicy.enabled` exists, and ideally defaults to `true`.

Templates:

- Strings are quoted: `{{ .Values.env.LOG_LEVEL | quote }}`. Unquoted `yes`, `no`, `on`, `1.10` or `0755` change type in YAML.
- `tpl` is applied only to values the chart author controls. `tpl` on user input lets the value read `.Values`, `.Release` and run `lookup`.
- `lookup` returns an empty map under `helm template` and plain `--dry-run`. Templates must handle the empty case and not generate a new random password on every upgrade.
- Secret values go into `kind: Secret` or are referenced from an existing secret (`existingSecret`). Never into a ConfigMap, a pod annotation, an env `value`, or `NOTES.txt`.
- `NOTES.txt` prints commands to fetch a secret (`kubectl get secret ...`), not the secret itself.
- Use `toYaml` with `nindent` for nested blocks so a user override cannot break indentation.
- `required` guards values the chart cannot run without: `{{ required "image.repository is required" .Values.image.repository }}`.
- Labels follow `app.kubernetes.io/*` so selectors and NetworkPolicies match.

Chart.yaml and Chart.lock:

- `apiVersion: v2`, `version` bumped on every change, `appVersion` matches the image.
- Dependency `version` pinned (`12.5.6` or `~12.5.6`), not `*` or `>=0`.
- `Chart.lock` committed. `charts/*.tgz` either committed on purpose or rebuilt in CI with `helm dependency build`.
- Repositories are `https://` or `oci://`, never `http://`.

Provenance and distribution:

- Classic repos: `helm package --sign --key 'Release Key' --keyring ~/.gnupg/secring.gpg ./chart` produces a `.prov`; consumers run `helm verify` or `helm install --verify`.
- OCI: `helm push app-1.2.3.tgz oci://registry.example.com/charts`, then sign the pushed digest with cosign and verify before install.
- Installs pin `--version`, never the newest chart by default.

Secrets:

- helm-secrets with SOPS for encrypted values files, decrypted only at deploy time.
- External Secrets Operator: the chart ships an `ExternalSecret`, the value lives in the vault.
- Sealed Secrets: `kubeseal --format yaml < secret.yaml > sealed-secret.yaml`; only the sealed file goes in git.

## Output format

| Severity | File | Line | Area | Issue | Fix |
|---|---|---|---|---|---|
| Critical | charts/api/templates/configmap.yaml | 9 | Template | `.Values.db.password` rendered into ConfigMap | Move to Secret or `existingSecret` reference |
| High | charts/api/values.yaml | 14 | Defaults | `securityContext: {}`, pod runs as root | Set restricted defaults (see patch) |
| High | charts/api/templates/deployment.yaml | 31 | Template | `tpl .Values.extraEnv .` on user input | Render with `toYaml`, drop `tpl` |
| Medium | charts/api/Chart.yaml | 18 | Dependencies | `postgresql` version `*`, no Chart.lock | Pin `12.5.6`, commit Chart.lock |
| Low | charts/api | - | Schema | No `values.schema.json` | Add schema for security-relevant keys |

After the table:

1. Patches against `values.yaml` and the template files for Critical and High.
2. Scanner summary (tool, version, counts) and false positives with reasons.
3. Provenance and secrets status: signed or not, how installs verify, where secret values live.

Severity: Critical (secret leaked into rendered output or git, privileged or hostPath by default), High (root by default, `tpl` on user input, wildcard RBAC by default, unsigned chart from an untrusted source), Medium (unpinned dependencies or image tag, no resources, no schema on a published chart), Low (labels, docs, lint warnings).

## Examples

Bad `values.yaml` and template: root by default, `latest` tag, token mounted, password in a ConfigMap.

```yaml
# values.yaml
image:
  repository: registry.example.com/api
  tag: latest
securityContext: {}
resources: {}
db:
  password: "example-password-not-real"
```

```yaml
# templates/configmap.yaml
data:
  DB_PASSWORD: {{ .Values.db.password }}
  LOG_LEVEL: {{ .Values.logLevel }}
```

Good: restricted defaults, digest support, secret from an existing Secret, quoted values.

```yaml
# values.yaml
image:
  repository: registry.example.com/api
  tag: "1.4.2"
  digest: ""
serviceAccount:
  create: true
  automount: false
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 10001
  seccompProfile:
    type: RuntimeDefault
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
resources:
  requests: { cpu: 100m, memory: 256Mi }
  limits: { memory: 512Mi }
db:
  existingSecret: api-db
logLevel: info
```

```yaml
# templates/deployment.yaml (excerpt)
image: "{{ .Values.image.repository }}{{ if .Values.image.digest }}@{{ .Values.image.digest }}{{ else }}:{{ .Values.image.tag }}{{ end }}"
securityContext:
  {{- toYaml .Values.securityContext | nindent 2 }}
env:
  - name: LOG_LEVEL
    value: {{ .Values.logLevel | quote }}
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ required "db.existingSecret is required" .Values.db.existingSecret }}
        key: password
```
