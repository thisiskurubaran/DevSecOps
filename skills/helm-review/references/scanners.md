# Scanners for Helm charts

Some tools read the chart directory and render it themselves. Others need the output of `helm template`. Render with the values you actually deploy, or the scan reviews a configuration nobody runs.

```bash
helm template rel ./chart -f values-prod.yaml > rendered-prod.yaml
```

| Tool | Input | Command | Catches |
|---|---|---|---|
| helm lint | chart dir | `helm lint ./chart --strict -f values-prod.yaml` | Template errors, missing required fields, schema violations |
| chart-testing | repo | `ct lint --config ct.yaml --target-branch main` | Lint, version bump checks, maintainer and YAML checks on changed charts |
| chart-testing | repo + cluster | `ct install --config ct.yaml --target-branch main` | Chart installs and its tests pass on a real cluster (kind works) |
| kubeconform | rendered | `kubeconform -strict -summary -kubernetes-version 1.30.0 rendered-prod.yaml` | Schema errors, unknown fields, removed APIs |
| kube-score | rendered | `kube-score score rendered-prod.yaml` | Security context, probes, resources, NetworkPolicy coverage |
| Checkov | chart dir | `checkov -d ./chart --framework helm` | CKV_K8S_* policies on rendered templates |
| Trivy | chart dir | `trivy config ./chart` | Misconfigurations in rendered templates |
| kube-linter | chart dir | `kube-linter lint ./chart` | Privileged containers, missing limits, writable root fs, default SA |
| Polaris | rendered | `polaris audit --audit-path rendered-prod.yaml --format pretty` | Security, efficiency and reliability score per workload |

Notes:

- Scan the default render too (`helm template rel ./chart`). Insecure defaults hide behind a hardened production values file.
- `lookup` returns nothing during `helm template`, so resources built from it may be missing from the scan. Note this as a coverage gap.
- Run the chart's own tests after install with `helm test rel`.
- Record tool versions in the report. Rule IDs and defaults change between releases.
