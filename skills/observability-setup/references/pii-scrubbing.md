# Keeping PII and secrets out of telemetry

Telemetry often ends up with wider access and longer retention than the production database. Treat it as a data store that needs the same care.

## What to keep out

| Data | Where it leaks | Fix |
|---|---|---|
| Bearer tokens, session cookies | Request header logging, `http.request.header.*` span attributes | Header allowlist; delete in Collector |
| API keys in query strings | Access logs, `url.full`, `url.query` | Strip query strings or redact known param names (`token`, `key`, `sig`) |
| Passwords | Form body logging, validation error messages | Never log bodies; redact `password` keys in logger config |
| Emails, names, phone numbers | Log messages, user labels, span attributes | Use opaque user IDs |
| Card numbers (PAN) | Payment request bodies, error dumps | Never log; Collector regex backstop; PCI DSS 3.3 and 10.3 |
| SQL bound values | DB span statements, ORM debug logs | Sanitized statements only; ORM query logging off in prod |
| IP addresses | Access logs | Truncate or hash if not needed; check GDPR basis |
| Stack traces with locals | Error trackers (Sentry, Rollbar) | Disable locals capture or scrub (`send_default_pii=False`, `before_send`) |

## Layers

1. Source: logger redact config and serializers that pick fields instead of dumping objects.
2. SDK: OpenTelemetry instrumentation options that limit captured headers and sanitize DB statements.
3. Collector: `attributes`, `redaction`, `transform` processors. Catches what services miss.
4. Backend: retention limits, access control, and audit on who queries logs.

## Logger redaction by language

Node (pino):

```js
pino({ redact: { paths: ["req.headers.authorization", "req.headers.cookie", "*.password", "*.card_number"], remove: true } })
```

Python (structlog):

```python
SENSITIVE = {"password", "token", "authorization", "card_number", "email"}

def redact(_, __, event_dict):
    for k in list(event_dict):
        if k.lower() in SENSITIVE:
            event_dict[k] = "[REDACTED]"
    return event_dict

structlog.configure(processors=[redact, structlog.processors.JSONRenderer()])
```

Go (slog):

```go
h := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    ReplaceAttr: func(_ []string, a slog.Attr) slog.Attr {
        switch strings.ToLower(a.Key) {
        case "password", "token", "authorization", "email":
            return slog.String(a.Key, "[REDACTED]")
        }
        return a
    },
})
```

Java (Logback): use `logstash-logback-encoder` with a `MaskingJsonGeneratorDecorator` and `<path>` or `<value>` masks.

## OpenTelemetry SDK settings

| Setting | Purpose |
|---|---|
| `OTEL_INSTRUMENTATION_HTTP_SERVER_CAPTURE_REQUEST_HEADERS=x-request-id,user-agent` | Java agent header allowlist (similar options exist per language) |
| `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=1024` | Caps very long attribute values |
| Node `@opentelemetry/instrumentation-http` `headersToSpanAttributes` | Explicit header allowlist |
| DB instrumentations `enhancedDatabaseReporting: false` | Avoid bound parameter capture |

## Collector processors

```yaml
processors:
  transform/url:
    trace_statements:
      - context: span
        statements:
          - replace_pattern(attributes["url.full"], "([?&](token|key|sig|code)=)[^&]*", "$$1REDACTED")
          - delete_key(attributes, "url.query")
    log_statements:
      - context: log
        statements:
          - replace_pattern(body, "(?i)(authorization: *bearer )[A-Za-z0-9._-]+", "$$1REDACTED")
```

The `redaction` processor can also run in allowlist mode (`allow_all_keys: false` with `allowed_keys: [...]`). That is stricter and catches new attributes nobody reviewed, but expect to tune it.

## Verifying

Before calling setup done, sample real output:

```sh
# Look for emails, JWTs and card-like numbers in a log export
grep -EnI '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|\b[0-9]{13,16}\b' logs-sample.json | head
```

Also query the backend directly, for example in Loki: `{service_name="api"} |~ "(?i)bearer [a-z0-9]"`.
