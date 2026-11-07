---
name: policy-as-code
description: Write and test OPA/Rego, Conftest, Gatekeeper and Kyverno policies, and map each rule to SOC 2, ISO 27001 or PCI DSS controls. Use when the user asks to write a Rego or Kyverno policy, enforce a guardrail in CI or at Kubernetes admission, add policy unit tests, or produce a control-to-policy mapping for an audit.
---

# Policy as Code

Turn a written rule ("no public S3 buckets", "containers must not run as root") into a policy that a machine enforces, with tests, a clear deny message, and a link back to the compliance control it satisfies.

## When to use

- The user wants an OPA/Rego policy for Terraform plans, Kubernetes manifests, Dockerfiles or JSON/YAML config, run through `conftest` or `opa eval`.
- The user wants a Kyverno `ClusterPolicy` or a Gatekeeper `ConstraintTemplate` plus `Constraint` for admission control.
- Existing policies have no tests, deny too much, or give messages nobody can act on.
- An auditor or GRC team needs a table showing which policy enforces which SOC 2, ISO 27001 or PCI DSS control.

Not for: one-off review of a Terraform module (use `iac-review`) or a set of manifests (use `k8s-manifest-review`). Use those to find problems, and this skill to stop them coming back. Wiring the policy step into a pipeline belongs to `cicd-pipeline-builder`.

## Steps

1. Write the rule in one plain sentence, including scope and exceptions. Example: "Every `aws_s3_bucket` in prod must block public access, except buckets tagged `public-website=true`."
2. Pick the engine by where the check runs:
   - CI on Terraform plans, Helm output, Dockerfiles, generic config: OPA with `conftest`.
   - Kubernetes admission, Kubernetes-native team: Kyverno.
   - Kubernetes admission where OPA is already standard: Gatekeeper.
   - Cloud account level: native tools (AWS SCPs, Azure Policy, GCP Org Policy). Say so instead of forcing Rego.
3. Get real input. For Terraform run `terraform plan -out tf.plan && terraform show -json tf.plan > plan.json`. For Kubernetes use rendered manifests (`helm template`, `kustomize build`). Write the policy against that shape, not against guessed field names.
4. Write the policy with `import rego.v1` (OPA 1.0 syntax: `if`, `contains`). Use a `deny contains msg if` rule for blocking and `warn contains msg if` for advisory checks. Put the resource address and the fix in the message.
5. Add an exception path that is explicit and auditable: a label, tag or annotation with an owner and expiry, or a data file of allowed IDs. No silent wildcards.
6. Write tests next to the policy (`*_test.rego` or Kyverno CLI test files). Cover one passing input, one failing input, and the exception. Run `opa test -v policy/` or `kyverno test .`.
7. Roll out in audit mode first: Kyverno `validationFailureAction: Audit`, Gatekeeper `enforcementAction: dryrun`, conftest `warn` rules. Check reports for a week, fix false positives, then switch to `Enforce`/`deny`.
8. Add the control mapping. Each policy gets metadata with the control IDs it supports. See [references/control-mapping.md](references/control-mapping.md) for common mappings.
9. Run formatting and lint: `opa fmt -w`, `opa check --strict`, and `regal lint` if available.

## Checklist

Rego and Conftest:

- `package` name matches the folder (`package terraform.s3` in `policy/terraform/s3/`).
- Uses `import rego.v1`. No deprecated `deny[msg] { ... }` syntax in new code.
- Iterates with `some r in input.resource_changes`, and filters on `r.change.actions` so deletes are not flagged.
- Reads `r.change.after`, not `r.change.before`, for planned state.
- Handles missing fields with `object.get` or a default, so an absent attribute fails closed when it should.
- Messages include the resource address (`r.address`) and what to change.
- `opa test` coverage: `opa test --coverage policy/ | jq .coverage` above 80 percent for the policy files.
- `conftest test plan.json -p policy/ --all-namespaces` runs in CI and fails the job on `deny`.

Kyverno:

- `validationFailureAction` set explicitly (`Audit` during rollout, `Enforce` after).
- `background: true` so existing resources show up in `PolicyReport`.
- `match` and `exclude` blocks scope by kind and namespace; `kube-system` and the Kyverno namespace excluded where needed.
- Pod rules use `autogen` so Deployments, StatefulSets and Jobs are covered.
- `kyverno test` cases exist for pass, fail and skip.
- `failurePolicy: Fail` for security rules, with a webhook timeout set.

Gatekeeper:

- `ConstraintTemplate` Rego has `violation[{"msg": msg}]` and reads `input.review.object`.
- Constraint `match.kinds` and `excludedNamespaces` set.
- `enforcementAction: dryrun` first, then `deny`.
- `gator verify` suite for each template.

Mapping and governance:

- Each policy has metadata: id, title, severity, owner, control IDs.
- Exceptions have an owner and an expiry date, and are reviewed.
- Policy repo has CODEOWNERS so security reviews changes to the rules.

## Output format

Deliver the policy files, the test files, and this summary:

```markdown
## Policies

| ID | Engine | Rule | Mode | Severity | Controls |
|---|---|---|---|---|---|
| S3-001 | conftest | S3 buckets block public access | deny | high | SOC 2 CC6.1, ISO 27001 A.8.3, PCI DSS 1.4.1 |

## Files
- policy/terraform/s3/public_access.rego
- policy/terraform/s3/public_access_test.rego

## How to run
conftest test plan.json -p policy/
opa test -v policy/

## Rollout
Audit until <date>, then enforce. Exceptions: tag `public-website=true` plus `exception-owner`.
```

When reviewing existing policies, use a findings table:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| medium | policy/k8s/root.rego | 12 | Checks `containers` only, misses `initContainers` | Iterate over both lists |

## Examples

Bad: old syntax, no resource address, flags deletes, no test.

```rego
package main

deny[msg] {
  r := input.resource_changes[_]
  r.type == "aws_s3_bucket_public_access_block"
  r.change.after.block_public_acls == false
  msg = "bad bucket"
}
```

Good: OPA 1.0 syntax, skips deletes, fails closed on a missing value, actionable message, explicit exception.

```rego
package terraform.s3

import rego.v1

# METADATA
# title: S3 public access block required
# custom:
#   id: S3-001
#   severity: high
#   controls: ["SOC2:CC6.1", "ISO27001:A.8.3", "PCI:1.4.1"]

flags := ["block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"]

deny contains msg if {
  some r in input.resource_changes
  r.type == "aws_s3_bucket_public_access_block"
  not "delete" in r.change.actions
  some f in flags
  object.get(r.change.after, f, false) != true
  not exempt(r)
  msg := sprintf("%s: set %s = true (S3-001)", [r.address, f])
}

# data/exceptions.json: {"exceptions": {"s3": {"aws_s3_bucket_public_access_block.site": {"owner": "web-team", "expires": "2027-01-31"}}}}
exempt(r) if {
  e := data.exceptions.s3[r.address]
  time.parse_ns("2006-01-02", e.expires) > time.now_ns()
}
```

Test:

```rego
package terraform.s3_test

import rego.v1
import data.terraform.s3

test_open_bucket_denied if {
  count(s3.deny) > 0 with input as {"resource_changes": [{
    "address": "aws_s3_bucket_public_access_block.logs",
    "type": "aws_s3_bucket_public_access_block",
    "change": {"actions": ["create"], "after": {"block_public_acls": false}},
  }]}
}

test_delete_ignored if {
  count(s3.deny) == 0 with input as {"resource_changes": [{
    "address": "aws_s3_bucket_public_access_block.old",
    "type": "aws_s3_bucket_public_access_block",
    "change": {"actions": ["delete"], "after": null},
  }]}
}
```

Kyverno, good: audit first, autogen covers controllers, clear message.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-run-as-non-root
  annotations:
    policies.kyverno.io/title: Require runAsNonRoot
    policies.kyverno.io/severity: high
    example.com/controls: "SOC2:CC6.8, ISO27001:A.8.9, PCI:2.2.1"
spec:
  validationFailureAction: Audit
  background: true
  rules:
    - name: run-as-non-root
      match:
        any:
          - resources:
              kinds: ["Pod"]
      exclude:
        any:
          - resources:
              namespaces: ["kube-system", "kyverno"]
      validate:
        message: "Set securityContext.runAsNonRoot: true on the pod or on every container."
        anyPattern:
          - spec:
              securityContext:
                runAsNonRoot: true
              containers:
                - =(securityContext):
                    =(runAsNonRoot): true
          - spec:
              containers:
                - securityContext:
                    runAsNonRoot: true
```
