# Security header config by stack

Starting points for each stack. Adjust the CSP to the page inventory from the skill's steps, and start with `Content-Security-Policy-Report-Only` before enforcing.

## nginx

```nginx
server_tokens off;                  # "Server: nginx" without the version
proxy_hide_header X-Powered-By;     # strip the upstream app's header

server {
    listen 443 ssl;
    server_name example.com;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Content-Security-Policy "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'" always;
}

server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
```

Gotchas:

- `always` makes nginx add the header on error responses (4xx, 5xx) too.
- `add_header` is inherited only if the current level defines none. One `add_header` inside a `location` block drops every header from the `server` block for that location. Put the shared set in a snippet and `include` it in each block that adds its own headers.
- nginx cannot generate a per-request nonce by itself. Let the app set CSP, or use hashes for static pages.

## Express with helmet

```js
const crypto = require("node:crypto");
const helmet = require("helmet");

app.use((req, res, next) => {
  res.locals.cspNonce = crypto.randomBytes(16).toString("base64");
  next();
});

app.use(helmet({
  contentSecurityPolicy: {
    useDefaults: false,
    directives: {
      scriptSrc: [(req, res) => `'nonce-${res.locals.cspNonce}'`, "'strict-dynamic'"],
      objectSrc: ["'none'"],
      baseUri: ["'none'"],
      frameAncestors: ["'none'"],
      formAction: ["'self'"],
    },
    reportOnly: false, // true while rolling out
  },
  strictTransportSecurity: { maxAge: 31536000, includeSubDomains: true },
  referrerPolicy: { policy: "strict-origin-when-cross-origin" },
}));
```

- helmet removes `X-Powered-By`. Without helmet, call `app.disable("x-powered-by")`.
- Render the nonce into templates: `<script nonce="<%= cspNonce %>">`.
- helmet does not set `Permissions-Policy`. Set it with `res.setHeader` in a small middleware.
- Cookies: `res.cookie("__Host-session", value, { secure: true, httpOnly: true, sameSite: "lax", path: "/" })`.

## Next.js

Static headers in `next.config.js`:

```js
module.exports = {
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};
```

Nonce-based CSP needs per-request code, so it goes in middleware (`middleware.ts`; newer releases rename the file, check the docs for your version):

```ts
import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = `script-src 'nonce-${nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`;

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}
```

Next.js reads the nonce from the request CSP header and applies it to its own scripts. Pages using a nonce must render dynamically, not as cached static HTML.

## Django

```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # only behind a proxy that sets it
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
```

These need `django.middleware.security.SecurityMiddleware` and `django.middleware.clickjacking.XFrameOptionsMiddleware` in `MIDDLEWARE`. Run `python manage.py check --deploy` to catch missing settings.

CSP with django-csp 4.x (add `csp.middleware.CSPMiddleware` to `MIDDLEWARE`):

```python
from csp.constants import NONCE, NONE, SELF, STRICT_DYNAMIC

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "script-src": [NONCE, STRICT_DYNAMIC],
        "object-src": [NONE],
        "base-uri": [NONE],
        "frame-ancestors": [NONE],
        "form-action": [SELF],
        "report-uri": "/csp-reports",
    },
}
# Use CONTENT_SECURITY_POLICY_REPORT_ONLY with the same shape while rolling out.
```

Template: `<script nonce="{{ request.csp_nonce }}">`. django-csp 3.x used flat `CSP_*` settings; check which version the project pins. Django 6.0 added built-in CSP support; if the project is on 6.0 or later, check the Django docs before adding django-csp.

## Spring Security (6.x, Java config)

```java
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp
        .policyDirectives("script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"))
    .httpStrictTransportSecurity(hsts -> hsts
        .includeSubDomains(true)
        .maxAgeInSeconds(31536000))
    .frameOptions(frame -> frame.deny())
    .referrerPolicy(ref -> ref
        .policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))
);
```

- Spring Security sends `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, HSTS (on HTTPS requests) and cache control headers by default. Adding `.headers(...)` customizes them; it does not turn them off unless you call `.disable()`.
- `.contentSecurityPolicy(csp -> csp.policyDirectives(...).reportOnly())` sends the report-only header.
- Spring Security has no built-in CSP nonce. Generate one in a filter and set the header yourself, or use hashes.
- Session cookie flags in Spring Boot: `server.servlet.session.cookie.secure=true`, `server.servlet.session.cookie.http-only=true`, `server.servlet.session.cookie.same-site=lax`.

## CloudFront response headers policy

Terraform:

```hcl
resource "aws_cloudfront_response_headers_policy" "security" {
  name = "security-headers"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = false
      override                   = true
    }
    content_type_options {
      override = true
    }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    content_security_policy {
      content_security_policy = "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
      override                = true
    }
  }

  custom_headers_config {
    items {
      header   = "Permissions-Policy"
      value    = "camera=(), microphone=(), geolocation=()"
      override = true
    }
  }

  remove_headers_config {
    items {
      header = "Server"
    }
    items {
      header = "X-Powered-By"
    }
  }
}
```

Attach it with `response_headers_policy_id` on the cache behavior. AWS also ships a managed `Managed-SecurityHeadersPolicy`; check its values before relying on it. A response headers policy is static, so it cannot add a per-request nonce: use hashes for static sites, or set CSP at the origin or in an edge function.

## Verify

```bash
curl -sI https://example.com/ | grep -iE 'content-security|strict-transport|x-content-type|referrer-policy|permissions-policy|cross-origin|x-frame|set-cookie|server|x-powered-by'

# CORS: an unknown origin should get no Access-Control-Allow-Origin back
curl -sI -H "Origin: https://evil.example.net" https://example.com/api/me | grep -i access-control

# Preflight
curl -si -X OPTIONS https://example.com/api/me \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" | grep -i access-control
```

Then run the site through MDN HTTP Observatory and paste the CSP into Google CSP Evaluator.
