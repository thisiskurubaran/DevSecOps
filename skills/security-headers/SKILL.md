---
name: security-headers
description: Write and review HTTP security headers and browser hardening (Content-Security-Policy with nonces or hashes and strict-dynamic, HSTS and preload, CORS allowlists, cookie flags and __Host- prefix, Referrer-Policy, Permissions-Policy, COOP/COEP/CORP, frame-ancestors, removing X-Powered-By and Server leaks) for nginx, Express with helmet, Next.js, Django, Spring Security and CloudFront, verified with curl -sI. Use when the user shares response headers, a header or CORS config, asks how to add or fix CSP, HSTS or cookie flags, gets a low Observatory grade, or opens a PR that changes web server, middleware or CDN header settings.
---

# Security Headers

Headers are cheap to add and easy to get subtly wrong: a CSP with `'unsafe-inline'` that blocks nothing, HSTS preloaded on a domain with an HTTP-only subdomain, a CORS handler that echoes any `Origin` with credentials. Read what the server actually sends, then fix the config that produces it.

## When to use

- The user pastes `curl -I` output, a HAR, or a browser console CSP violation and asks what to change.
- The user shares nginx, Apache, Caddy, helmet, `next.config.js`, Django settings, Spring Security config, or a CloudFront response headers policy.
- The user asks "how do I add a CSP without breaking the site", "is my CORS config safe", "should I preload HSTS", or "why is my Observatory grade an F".
- A PR touches header middleware, CORS setup, cookie or session settings, or CDN/edge header rules.

Not for: finding XSS or injection in application code (use `security-audit`; CSP is a backstop, not the fix), session and token logic such as cookie lifetime, rotation or JWT handling (use `auth-review`), setting up and running ZAP or other DAST scanners (use `dast-setup`), or endpoint-level API review including authz and rate limits (use `api-security-review`).

## Steps

1. Capture what is sent today. Check several response types, because headers often differ per route:
   - `curl -sI https://example.com/` (HTML page)
   - `curl -sI https://example.com/api/health` (API)
   - `curl -sI https://example.com/static/app.js` (static asset, often served by a different layer)
   - `curl -sI http://example.com/` (should be a 301/308 to HTTPS, no HSTS needed here)
2. Find where each header is set: app middleware, reverse proxy, CDN, or load balancer. Duplicates from two layers cause two CSP headers (both enforced, so the strictest wins) or conflicting values.
3. Review against the checklist. Note missing headers, weak values, and leaks.
4. For CSP, inventory the page first: inline scripts, inline event handlers (`onclick=`), `eval` or `new Function`, third-party script hosts, iframes. Inline handlers and `eval` must be refactored or the policy will not hold.
5. Pick a CSP style. Server-rendered pages: nonce per response. Static sites or CDN-only: hashes (`'sha256-...'`). Add `'strict-dynamic'` so scripts loaded by trusted scripts work without host allowlists.
6. Roll out CSP in report-only mode first: send `Content-Security-Policy-Report-Only` with a reporting endpoint, watch reports for a week or a full release cycle, fix violations, then switch to the enforcing header. Keep report-only running alongside when tightening later.
7. Roll out HSTS in steps: `max-age=300`, then a week, then a year. Add `includeSubDomains` only after confirming every subdomain serves HTTPS. Add `preload` last, if at all.
8. Write the fix in the user's stack. See [references/stack-config.md](references/stack-config.md) for nginx, Express, Next.js, Django, Spring Security and CloudFront.
9. Verify with `curl -sI` again, then an Observatory-style check (MDN HTTP Observatory, Google CSP Evaluator for the policy, hstspreload.org before preloading).
10. Report using the output format.

## Checklist

Content-Security-Policy:

- Strict baseline for script: `script-src 'nonce-{random}' 'strict-dynamic'; object-src 'none'; base-uri 'none'` (or `base-uri 'self'`).
- Nonce is at least 128 bits from a CSPRNG, new on every response, never cached in a shared HTML cache.
- No `'unsafe-inline'` in `script-src` unless it is a fallback next to a nonce or hash (browsers that support nonces ignore it then). No `'unsafe-eval'` unless a dependency truly needs it, and say which.
- No wildcards like `https:` or `*` as the only script source, and no hosts that serve user content or JSONP (CDNs with open uploads, `*.googleapis.com` style allowlists).
- `frame-ancestors 'none'` (or `'self'`) for clickjacking. It only works as a header, not in a `<meta>` tag. Same for `report-uri`, `report-to` and `sandbox`.
- `form-action 'self'` where forms post only to the same origin.
- Reporting: `report-to csp-endpoint` with a `Reporting-Endpoints: csp-endpoint="https://example.com/csp-reports"` header, plus `report-uri /csp-reports` as a fallback for browsers that do not support `report-to`.
- The report endpoint rate limits and does not log report bodies with tokens from URLs unredacted.

Strict-Transport-Security:

- Only sent over HTTPS. `max-age=31536000` (one year) or more once stable.
- `includeSubDomains` only when every subdomain, including internal tools and legacy hosts, works on HTTPS.
- `preload` requires `max-age` of at least 31536000 plus `includeSubDomains`, and is hard to undo: removal from browser lists takes months. Submit only at hstspreload.org after checking its requirements.

CORS:

- Never reflect the request `Origin` into `Access-Control-Allow-Origin` with `Access-Control-Allow-Credentials: true`. Match against an explicit allowlist of full origins.
- No suffix or regex matching that `example.com.attacker.net` or `attackerexample.com` can pass. Do not allow the `null` origin.
- `Access-Control-Allow-Origin: *` is fine for truly public, unauthenticated resources only. Browsers reject `*` with credentials.
- Send `Vary: Origin` when the response depends on the origin, so caches do not serve one origin's headers to another.
- `Access-Control-Max-Age` set (for example 600) to cut preflights; browsers cap it (Chromium at 7200 seconds).
- Allowed methods and headers listed explicitly, not echoed from `Access-Control-Request-*`.

Cookies:

- Session and auth cookies: `Secure; HttpOnly; SameSite=Lax` (or `Strict`), `Path=/`.
- `__Host-` prefix for session cookies: requires `Secure`, `Path=/` and no `Domain`, which pins the cookie to one host.
- `SameSite=None` only when cross-site use is needed, and it requires `Secure`.

Other headers:

- `X-Content-Type-Options: nosniff` on every response.
- `Referrer-Policy: strict-origin-when-cross-origin` or stricter (`no-referrer`, `same-origin`).
- `Permissions-Policy` disabling features the site does not use: `camera=(), microphone=(), geolocation=(), payment=()`.
- `Cross-Origin-Opener-Policy: same-origin` for pages that do not need popups to keep a window reference (use `same-origin-allow-popups` for OAuth popup flows).
- `Cross-Origin-Embedder-Policy: require-corp` (or `credentialless`) only when cross-origin isolation is needed, for example `SharedArrayBuffer`. It breaks third-party embeds that do not opt in.
- `Cross-Origin-Resource-Policy: same-origin` (or `same-site`) on API and private resources.
- `X-Frame-Options: DENY` as a fallback for old browsers. When both are present, browsers that support `frame-ancestors` ignore `X-Frame-Options`.
- `X-XSS-Protection` either absent or `0`. The old auditor is gone and `1; mode=block` caused issues.
- No `X-Powered-By`, no version in `Server` (`nginx/1.25.3`, `Apache/2.4.58 (Ubuntu)`), no `X-AspNet-Version` or framework debug headers.
- Cache: `Cache-Control: no-store` on responses with personal data or tokens.

## Output format

| Severity | Header / Setting | Where set | Current value | Issue | Fix |
|---|---|---|---|---|---|
| Critical | Access-Control-Allow-Origin | src/server.js:22 | reflects request `Origin`, credentials true | Any site can read authenticated API responses | Check origin against an allowlist, add `Vary: Origin` |
| High | Content-Security-Policy | nginx/site.conf:14 | `script-src 'self' 'unsafe-inline'` | Inline script injection not blocked | Nonce-based policy with `'strict-dynamic'`, report-only first |
| Medium | Server | nginx/nginx.conf | `nginx/1.25.3` | Version leak | `server_tokens off;` |

After the table:

1. Fixed config for each Critical and High, in the user's stack.
2. The full header set you recommend, as it should appear in `curl -sI` output.
3. Rollout notes: CSP report-only period, HSTS `max-age` steps, what might break (third-party widgets, embeds, OAuth popups).
4. Anything you could not judge without more context (for example, "do any subdomains still serve plain HTTP?").

Severity: Critical (CORS that exposes authenticated data cross-origin, session cookies without `Secure` or `HttpOnly` on an auth app), High (no CSP or a CSP that allows inline script on an app with user content, no HSTS on a login site, no clickjacking protection on sensitive actions), Medium (weak Referrer-Policy, missing `nosniff`, version leaks, HSTS without `includeSubDomains` where it is safe to add), Low (missing Permissions-Policy, obsolete headers left in place).

## Examples

Bad: CSP that blocks nothing, HSTS preloaded too early, CORS echoing any origin.

```
Content-Security-Policy: default-src * 'unsafe-inline' 'unsafe-eval'
Strict-Transport-Security: max-age=600; includeSubDomains; preload
Access-Control-Allow-Origin: https://evil.example.net
Access-Control-Allow-Credentials: true
Set-Cookie: sessionid=abc123; Path=/
X-Powered-By: Express
Server: nginx/1.25.3
```

Good: nonce-based strict CSP, stable HSTS, allowlisted CORS, hardened cookie, no leaks.

```
Content-Security-Policy: script-src 'nonce-q8P2kTzX9vLmN4rA1bC7dQ' 'strict-dynamic'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; report-to csp-endpoint; report-uri /csp-reports
Reporting-Endpoints: csp-endpoint="https://example.com/csp-reports"
Strict-Transport-Security: max-age=31536000; includeSubDomains
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
Set-Cookie: __Host-session=fake-session-value; Path=/; Secure; HttpOnly; SameSite=Lax
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
Server: nginx
```

Bad CORS handler in Express (reflects any origin with credentials):

```js
app.use(cors({ origin: true, credentials: true }));
```

Good:

```js
const allowed = ["https://app.example.com", "https://admin.example.com"];
app.use(cors({
  origin: (origin, cb) => cb(null, !origin || allowed.includes(origin)),
  credentials: true,
  maxAge: 600,
}));
```
