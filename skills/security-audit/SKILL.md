---
name: security-audit
description: Audit application source code for OWASP Top 10 issues (injection, broken access control, auth and session flaws, SSRF, insecure deserialization, XSS) and report each finding with severity, file, line and a code-level fix. Use when the user asks for a security audit or security review of a codebase, module, endpoint or auth flow, or asks "is this code safe" about request handling, login, sessions or database access.
---

# Security Audit

Read application code the way an attacker would: start where untrusted input enters, follow it to where it is used, and check every authorization decision on the way. Report only findings you can trace from source to sink, with a fix that fits the codebase.

## When to use

- The user asks to audit a service, module, endpoint or the whole repo for security bugs.
- The user wants an OWASP Top 10 review, or asks about injection, IDOR, auth bypass, XSS, SSRF or CSRF in specific code.
- A login, session, password reset, OAuth, file upload or admin feature is about to ship.
- The user pastes a handler and asks whether it is safe.

Not for: sorting existing scanner output (use `sast-dast-triage`), design-stage review with no code yet (use `threat-modeling`), CVEs in third-party packages (use `dependency-supply-chain`), hardcoded keys and rotation plans (use `secrets-management`), or general PR review (use `code-review`).

## Steps

1. Map the attack surface. List entry points: HTTP routes, GraphQL resolvers, gRPC methods, queue consumers, CLI args, file parsers, webhooks. Quick finds:
   - `grep -rnE "@(app|router)\.(get|post|put|delete|patch)|@RequestMapping|@GetMapping|router\.(get|post)|HandleFunc" src/`
   - Framework route files: `urls.py`, `routes.rb`, `routes/*.ts`, `config/routes.php`.
2. Identify the auth model. Where is authentication enforced (middleware, decorator, filter)? Where is authorization decided (per route, per object, policy engine)? List routes that skip the middleware.
3. Run a fast scanner pass to seed the review, not replace it:
   - `semgrep --config p/owasp-top-ten --config p/secrets --metrics=off .`
   - Language extras: `bandit -r src -ll` (Python), `gosec ./...` (Go), `brakeman` (Rails), `npm audit` is for deps, skip it here.
4. Trace sources to sinks. For each entry point, follow request params, headers, cookies, body fields and file names to dangerous sinks: SQL, shell, file paths, templates, HTML output, outbound URLs, deserializers, redirects, LDAP, XPath.
5. Check authorization per object. For every handler that takes an ID, confirm the query is scoped to the caller (`WHERE owner_id = :current_user`) or a policy check runs after loading.
6. Check auth and session handling against the checklist: password hashing, token validation, session cookies, reset flows, MFA, lockout.
7. Check config: debug flags, CORS, security headers, TLS settings, error handlers that leak stack traces.
8. Confirm each finding. Write the exact input that triggers it. If you cannot build one, mark it "needs verification" instead of reporting it as confirmed.
9. Rate severity with the table below and write the report. Fixes must be code in the project's language and framework.

## Checklist

A01 Broken access control

- Every route requiring login is behind auth middleware. Look for routes registered before the middleware or with `@AllowAnonymous`, `permit_all`, `skip_before_action :authenticate`.
- Object access is scoped to the caller or tenant (IDOR). Watch for `Model.find(params[:id])`, `findById(req.params.id)`, `get_object_or_404(Model, pk=pk)` with no owner filter.
- Role checks happen server side. No `isAdmin` read from the request body or a client-editable JWT claim without signature checks.
- CORS does not reflect arbitrary `Origin` with `Access-Control-Allow-Credentials: true`.

A02 Cryptographic failures

- Passwords hashed with argon2id, bcrypt (cost 12+), or scrypt. Not MD5, SHA-1, or unsalted SHA-256.
- No `Math.random()`, `random.random()` or `rand()` for tokens. Use `crypto.randomBytes`, `secrets.token_urlsafe`, `crypto/rand`.
- TLS verification not disabled: `verify=False`, `InsecureSkipVerify: true`, `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`.

A03 Injection

- SQL built with parameters or a query builder. Flag f-strings, `+` concatenation, `format()`, template literals, `.raw()`, `.extra()`, `knex.raw` with interpolation.
- No shell with input: `subprocess.run(..., shell=True)`, `os.system`, `child_process.exec`, `Runtime.exec(String)`. Use arg arrays.
- Templates auto-escape. Flag `|safe`, `mark_safe`, `dangerouslySetInnerHTML`, `v-html`, `{{{ }}}`, `html_safe`, `raw`.
- NoSQL: no `$where`, and query objects are not built from raw JSON bodies (`{ "$ne": null }` login bypass).

A04 Insecure design: business logic, rate limits on login, OTP and reset endpoints, race conditions on balances and coupons.

A05 Security misconfiguration

- `DEBUG = True`, `app.debug`, Spring Actuator or `/debug/pprof` exposed in production config.
- Security headers set: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `frame-ancestors`.
- XML parsers have external entities off (`defusedxml`, `XMLInputFactory.SUPPORT_DTD=false`).

A07 Identification and authentication failures

- JWT: algorithm pinned (`algorithms=["RS256"]`), `exp`, `aud`, `iss` checked, `none` rejected.
- Session cookies: `HttpOnly`, `Secure`, `SameSite=Lax` or `Strict`. Session ID rotated on login.
- Reset tokens single-use, expire within an hour, compared in constant time (`hmac.compare_digest`, `crypto.timingSafeEqual`).
- Login errors do not reveal whether the account exists.

A08 Software and data integrity failures: no `pickle.loads`, `yaml.load` without `SafeLoader`, Java native deserialization, or `unserialize()` on untrusted data.

A09 Logging and monitoring failures: auth failures and admin actions logged, tokens and passwords never logged.

A10 SSRF: user-supplied URLs fetched only after allowlist and post-DNS checks against private, loopback and link-local ranges (`169.254.169.254`). Redirects disabled or rechecked.

Also check: path traversal (`../` in file names, use `os.path.realpath` plus prefix check), open redirects (`next=` params), mass assignment (`Model(**request.json)`, `permit!`), CSRF on cookie-auth forms.

Per-framework sinks and safe APIs are in [references/framework-sinks.md](references/framework-sinks.md).

## Output format

Start with a two-line summary: scope audited and count by severity. Then one table, sorted by severity:

| # | Severity | OWASP | File | Line | Issue | Exploit sketch | Fix |
|---|----------|-------|------|------|-------|----------------|-----|

Severity:

| Level | Meaning |
|-------|---------|
| Critical | Unauthenticated RCE, auth bypass, SQLi on a reachable endpoint, cross-tenant data access at scale |
| High | Authenticated injection, IDOR on sensitive data, stored XSS, SSRF to metadata |
| Medium | Reflected XSS needing interaction, missing rate limit on login, weak token randomness |
| Low | Missing headers, verbose errors, defense-in-depth gaps |

After the table, add a "Needs verification" list for suspected issues you could not confirm, and a short "Not checked" list so the reader knows the limits.

## Examples

### Bad: SQL injection and IDOR in one handler (Python, Flask)

```python
@app.get("/api/orders/<order_id>")
@login_required
def get_order(order_id):
    row = db.execute(f"SELECT * FROM orders WHERE id = {order_id}").fetchone()
    return jsonify(dict(row))
```

`order_id=1 OR 1=1` dumps every order. Even with a numeric ID, any logged-in user reads any order.

### Good

```python
@app.get("/api/orders/<uuid:order_id>")
@login_required
def get_order(order_id):
    row = db.execute(
        "SELECT id, status, total FROM orders WHERE id = :id AND user_id = :uid",
        {"id": str(order_id), "uid": current_user.id},
    ).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))
```

Parameterized, scoped to the caller, returns only listed columns, and 404 for both "missing" and "not yours".

### Finding row

| # | Severity | OWASP | File | Line | Issue | Exploit sketch | Fix |
|---|----------|-------|------|------|-------|----------------|-----|
| 1 | Critical | A03, A01 | `app/orders.py` | 42 | f-string SQL and no owner filter | `GET /api/orders/1%20OR%201=1` returns all rows | Bind params and add `AND user_id = :uid` as shown above |
