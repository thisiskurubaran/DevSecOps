---
name: observability-setup
description: Set up structured logs, metrics, traces, alerts and SLOs with OpenTelemetry, Prometheus and Grafana, while keeping PII, secrets and tokens out of telemetry. Use when the user asks to add logging, metrics, tracing or alerting to a service, configure an OpenTelemetry Collector, define SLOs and burn-rate alerts, or check that logs do not leak personal data.
---

# Observability Setup

Instrument a service so that on-call can answer "is it broken, for whom, and where" in minutes, without the telemetry pipeline becoming a second copy of the user database.

## When to use

- A new or existing service has no structured logs, no metrics, or no traces.
- The user wants an OpenTelemetry SDK or Collector config, Prometheus scrape config, or Grafana dashboards.
- The user wants SLOs, error budgets and burn-rate alerts instead of CPU threshold alerts.
- Logs or spans may contain emails, tokens, card numbers or request bodies and need scrubbing.
- Alerts are noisy, unactionable, or missing runbook links.

Not for: tuning slow code paths found in traces (use `performance-review`), handling a live outage (use `incident-response`), or finding hardcoded secrets in source (use `secrets-management`).

## Steps

1. Inventory. Find the language, framework, existing logger, and where telemetry goes today (stdout, Datadog, Grafana Cloud, Elastic, CloudWatch). Do not add a second pipeline if one exists.
2. Pick the user journeys that matter (for example: login, checkout, API read). Each gets an SLI.
3. Logs: switch to structured JSON with a fixed field set: `timestamp`, `level`, `service.name`, `trace_id`, `span_id`, `message`, plus event-specific keys. Use the language's standard structured logger (`slog` in Go, `structlog` or `logging` with a JSON formatter in Python, `pino` in Node).
4. Metrics: expose RED metrics per endpoint (rate, errors, duration as a histogram) and USE metrics for resources. Prefer OpenTelemetry semantic convention names (`http.server.request.duration`). Keep label cardinality bounded.
5. Traces: add the OpenTelemetry SDK with auto-instrumentation for the HTTP server, HTTP client, DB driver and queue client. Propagate W3C `traceparent`. Sample at the Collector with tail sampling (keep all errors and slow traces, sample the rest).
6. Route everything through an OpenTelemetry Collector. Do PII scrubbing there with `attributes`, `redaction` and `transform` processors, so one config protects every service. See [references/pii-scrubbing.md](references/pii-scrubbing.md).
7. Also scrub at the source. Never log full request or response bodies, `Authorization` headers, cookies, or query strings with tokens. The Collector is the backstop, not the only line.
8. Define SLOs: target, window, SLI query. Example: 99.9 percent of `GET /api/*` return non-5xx within 500 ms over 28 days.
9. Alert on SLO burn rate using multi-window alerts (fast burn pages, slow burn files a ticket). Every alert has `severity`, `summary`, and a `runbook_url`.
10. Build one dashboard per service: SLO status and budget left at the top, then RED panels, then dependencies. Link dashboards from alerts.
11. Verify. Trigger a test error and confirm the log line, the metric increment, the trace and the trace-to-log link all show up. Grep a sample of real logs for PII patterns before declaring done.

## Checklist

Logs:

- JSON output to stdout; the platform ships it. No log files inside containers.
- Every line has `trace_id` and `span_id` when inside a request.
- Levels mean something: `error` needs action, `warn` is unusual but handled, `info` is a business event, `debug` off in prod.
- No `Authorization`, `Cookie`, `Set-Cookie`, `password`, `token`, `secret`, `api_key` fields. Logger has a redact list (`pino({ redact: [...] })`, structlog processor, `slog.HandlerOptions.ReplaceAttr`).
- User identified by an opaque ID, not email or name.
- Retention set per data class (for example 30 days app logs, 1 year audit logs) and access to log storage restricted.

Metrics:

- Histograms for latency, not averages. Buckets cover the SLO threshold.
- No user IDs, emails, full URLs or request IDs as label values. Use the route template (`/users/{id}`), not the raw path.
- `up` and scrape errors alerted on, so a dead exporter does not look like zero errors.
- Prometheus: `metric_relabel_configs` drop unused high-cardinality series.

Traces:

- `service.name`, `service.version`, `deployment.environment.name` set as resource attributes.
- `OTEL_EXPORTER_OTLP_ENDPOINT` points to the Collector, not directly to the vendor.
- DB spans record the statement with literals stripped (`db.query.text` sanitized), not bound values.
- `http.request.header.*` capture limited to an allowlist; never capture `authorization`.
- Tail sampling policies: all errors, all spans over the latency SLO, probabilistic for the rest.

Collector:

- `memory_limiter` first and `batch` last in every pipeline.
- `redaction` processor with `allow_all_keys: false` or a `blocked_values` regex list for card numbers, emails and JWTs.
- `attributes` processor deletes `http.request.header.authorization`, `user.email`, `enduser.id` if not needed.
- TLS on OTLP receivers exposed outside the cluster; exporters use `headers` from env, not inline keys.

Alerts and SLOs:

- Burn-rate alerts: 14.4x over 1h and 5m for paging, 6x over 6h and 30m for paging, 1x over 3d for a ticket (Google SRE workbook values for a 30 day window).
- Every alert has `runbook_url` and an owner.
- No alerts on causes alone (CPU 80 percent) unless they predict user impact.
- Alerts tested with `promtool test rules` or by firing in staging.

## Output format

When setting up, deliver config files plus:

```markdown
## Telemetry plan for <service>

| Signal | Tool | Destination | Retention | PII controls |
|---|---|---|---|---|
| Logs | pino JSON | OTel Collector -> Loki | 30d | redact list, Collector redaction |
| Metrics | OTel SDK | Collector -> Prometheus | 13 months | route templates only |
| Traces | OTel SDK auto-instr | Collector -> Tempo | 14d | header allowlist, tail sampling |

## SLOs
| SLI | Target | Window | Query |
|---|---|---|---|

## Alerts
| Name | Condition | Severity | Runbook |
|---|---|---|---|
```

When reviewing, use findings:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| high | src/middleware/log.ts | 18 | Logs `req.headers`, includes `authorization` | Log an allowlist of headers; add `redact: ["req.headers.authorization"]` |

## Examples

Bad: string logs, full body, raw email, token in the query string.

```js
app.use((req, res, next) => {
  console.log(`request ${req.method} ${req.url} ${JSON.stringify(req.body)} user=${req.user.email}`);
  next();
});
```

Good: structured, trace-linked, allowlisted fields, opaque ID, redaction as a backstop.

```js
const logger = pino({
  redact: { paths: ["req.headers.authorization", "req.headers.cookie", "*.password", "*.token"], remove: true },
});

app.use(pinoHttp({
  logger,
  serializers: {
    req: (req) => ({ method: req.method, route: req.routeOptions?.url ?? "unknown" }),
  },
  customProps: (req) => ({ user_id: req.user?.id }),
}));
```

Bad: metric label with unbounded values.

```python
REQUESTS.labels(path=request.path, user=user.email).inc()
```

Good: route template, no user label.

```python
REQUESTS.labels(route=request.url_rule.rule, method=request.method, code=str(status)).inc()
```

Good: Collector redaction, applied to every service.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
  attributes/strip:
    actions:
      - { key: http.request.header.authorization, action: delete }
      - { key: http.request.header.cookie, action: delete }
      - { key: user.email, action: delete }
  redaction:
    allow_all_keys: true
    blocked_values:
      - "\\b(?:\\d[ -]*?){13,16}\\b"                       # card numbers
      - "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"  # emails
      - "eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+" # JWTs
  batch: {}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, attributes/strip, redaction, batch]
      exporters: [otlp/tempo]
```

Good: burn-rate alert for a 99.9 percent SLO.

```yaml
- alert: ApiErrorBudgetFastBurn
  expr: |
    (sum(rate(http_requests_total{job="api",code=~"5.."}[1h])) / sum(rate(http_requests_total{job="api"}[1h]))) > (14.4 * 0.001)
    and
    (sum(rate(http_requests_total{job="api",code=~"5.."}[5m])) / sum(rate(http_requests_total{job="api"}[5m]))) > (14.4 * 0.001)
  labels:
    severity: page
  annotations:
    summary: "API burning error budget 14x too fast"
    runbook_url: https://runbooks.example.com/api/error-budget
```
