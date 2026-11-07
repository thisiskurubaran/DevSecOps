# Test prompts for k8s-manifest-review

How to test: copy `skills/k8s-manifest-review` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review the manifests in `k8s/` before we deploy to prod. I'm worried about RBAC and that nothing has resource limits."
2. "Here is our Helm chart's `values.yaml` and `deployment.yaml` template. Will it pass the Pod Security Standards restricted profile?"

## Should not trigger

1. "Write a Kyverno ClusterPolicy that blocks any pod running as root across the cluster."
   This belongs to `policy-as-code`.
