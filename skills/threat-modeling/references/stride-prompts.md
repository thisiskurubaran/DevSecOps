# STRIDE prompts by DFD element

Not every STRIDE category applies to every element type. Use this table to skip the ones that do not fit, then work through the prompts for the ones that do.

| Element | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| External entity | yes | | yes | | | |
| Process | yes | yes | yes | yes | yes | yes |
| Data store | | yes | yes | yes | yes | |
| Data flow | | yes | | yes | yes | |

## External entity (user, vendor, other service)

- Can someone pretend to be this entity? What credential proves identity, and where is it validated?
- Is there a shared secret (API key, webhook secret)? How is it rotated, and what happens if it leaks?
- Can the entity deny having sent a request? Is there a signed record or audit entry?

## Process (API, worker, lambda, cron job)

- Spoofing: does it accept requests from anything that can reach it on the network?
- Tampering: does it load code, templates, plugins or config from a path a user can write to?
- Repudiation: are state changes logged with actor and target, and can the process itself delete those logs?
- Information disclosure: do stack traces, debug endpoints (`/debug/pprof`, `/actuator`, `/_profiler`) or verbose errors reach callers?
- Denial of service: what input size, nesting depth or regex makes it spin? Are timeouts set on every outbound call?
- Elevation of privilege: does it run as root, with a broad cloud role, or with access to the container runtime socket? Does it deserialize untrusted data (`pickle`, Java `ObjectInputStream`, YAML `load`)?

## Data store (database, bucket, cache, queue, log store)

- Tampering: which identities can write? Is it one role per service or a shared admin user?
- Repudiation: are writes and deletes audited (CloudTrail data events, pgaudit, bucket access logs)?
- Information disclosure: encrypted at rest with a key the team controls? Public access blocked? Backups and snapshots under the same controls? Tenants separated by row filter, schema or database?
- Denial of service: storage quotas, connection limits, queue max depth and dead letter queue.

## Data flow (HTTP call, message, file transfer)

- Tampering: TLS on every hop, including inside the VPC? Messages signed if they cross accounts?
- Information disclosure: secrets or PII in URLs, query strings, headers that get logged? Payloads cached by a CDN or proxy?
- Denial of service: retries with backoff and jitter? Circuit breaker? Max payload size enforced at the edge?

## Feature-specific prompts

- File upload: type checked by content, size capped, stored outside web root, scanned, served from a separate domain with `Content-Disposition: attachment`.
- URL fetch: allowlist of hosts, block private and link-local ranges after DNS resolution, no redirects to internal hosts.
- Multi-tenant: tenant ID taken from the auth context, never from the request body. Cache keys include tenant.
- Admin and support tools: separate auth, MFA, every action audited, read-only by default.
- Payments and credits: idempotency keys, server-side price lookup, race conditions on balance updates.
- AI features: prompt injection from user content into tools with side effects, output rendered as HTML, model calls with secrets in context.
