# Rollout and rollback commands by platform

Pick the row that matches the deploy target. Test the rollback command in staging before the release, and write down how long it took.

## Kubernetes

| Action | Command |
|---|---|
| Watch a rollout | `kubectl rollout status deploy/api -n prod --timeout=10m` |
| Pause | `kubectl rollout pause deploy/api -n prod` |
| Roll back one revision | `kubectl rollout undo deploy/api -n prod` |
| Roll back to a revision | `kubectl rollout undo deploy/api -n prod --to-revision=41` |
| List revisions | `kubectl rollout history deploy/api -n prod` |

Set `revisionHistoryLimit` high enough (default 10) that the previous version still exists.

## Helm

| Action | Command |
|---|---|
| Deploy and wait, auto rollback on failure | `helm upgrade --install api ./chart -n prod --atomic --timeout 10m` |
| History | `helm history api -n prod` |
| Roll back | `helm rollback api 41 -n prod --wait` |

`--atomic` rolls back if pods do not become ready. It does not catch a release that is ready but returning errors.

## Argo Rollouts

```yaml
strategy:
  canary:
    steps:
      - setWeight: 5
      - pause: {duration: 15m}
      - analysis:
          templates: [{templateName: error-rate}]
      - setWeight: 50
      - pause: {duration: 30m}
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate
spec:
  metrics:
    - name: error-rate
      interval: 1m
      failureLimit: 3
      successCondition: result[0] < 0.01
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{app="api",code=~"5.."}[5m]))
            / sum(rate(http_requests_total{app="api"}[5m]))
```

Abort: `kubectl argo rollouts abort api -n prod`. Undo: `kubectl argo rollouts undo api -n prod`.

## AWS

| Target | Rollback |
|---|---|
| ECS | `aws ecs update-service --cluster prod --service api --task-definition api:41` |
| Lambda | Point the alias back: `aws lambda update-alias --function-name api --name live --function-version 41` |
| CodeDeploy | `aws deploy stop-deployment --deployment-id d-EXAMPLE --auto-rollback-enabled` |

Use Lambda aliases with weighted routing (`--routing-config AdditionalVersionWeights={"42"=0.05}`) for canaries.

## Packages and libraries

| Registry | Notes |
|---|---|
| npm | `npm deprecate pkg@1.4.0 "broken, use 1.4.1"`. Unpublish only within 72 hours and only if nothing depends on it. Publish a fixed patch instead. |
| PyPI | Yank the release in the web UI (pip skips yanked versions unless pinned). Publish a fixed patch. |
| Container images | Never overwrite a released tag. Push a new tag and update the deploy to the new digest. |

## Feature flags

Flags are the fastest rollback, since they need no deploy. For each flag in the release, record:

- name and default per environment
- who can flip it in prod
- what turning it off does to in-flight users and stored data
- removal date (flags left on for months turn into config debt)

## Database

- Expand and contract across at least two releases for renames, type changes and drops.
- Postgres: `CREATE INDEX CONCURRENTLY`, `ALTER TABLE ... ADD COLUMN` without a volatile default, and set `lock_timeout` (for example `SET lock_timeout = '5s'`) so a blocked migration fails instead of queueing every query behind it.
- MySQL: use `ALGORITHM=INPLACE, LOCK=NONE` where supported, or `gh-ost` / `pt-online-schema-change` for large tables.
- Down migrations are a last resort. Plan to roll forward with a fix if the schema change already ran.
