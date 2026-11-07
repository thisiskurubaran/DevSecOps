# Test prompts for gitops-security

How to test: copy `skills/gitops-security` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Three teams share one Argo CD. Here are our AppProjects and argocd-rbac-cm. Can team-a deploy into team-b's namespaces or create ClusterRoles?"
2. "We use Flux with a Kustomization per tenant. Review `clusters/prod/` and the controller flags. Do we need serviceAccountName and should we verify GitRepository commits?"

## Should not trigger

1. "Review this Deployment and Role in `deploy/prod/`. Is the security context OK and is the Role too broad?"
   This belongs to `k8s-manifest-review`.
