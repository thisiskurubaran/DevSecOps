# Test prompts for helm-review

How to test: copy `skills/helm-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "We're about to publish our internal `api` Helm chart to an OCI registry. Can you review `charts/api/` (values.yaml, templates, Chart.yaml) for security problems first?"
2. "This chart puts `.Values.db.password` into a ConfigMap and pulls the `postgresql` dependency with version `*`. What else is wrong with it and how do I fix the templates?"

## Should not trigger

1. "Review this Deployment and NetworkPolicy YAML in `k8s/prod/`. No Helm, just plain manifests."
   This belongs to `k8s-manifest-review`.
