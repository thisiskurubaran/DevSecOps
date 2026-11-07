# Security Policy

This repo holds Markdown skills and a few small helper scripts. A security
issue here usually means one of these:

- A skill gives advice that would make a system less secure (for example, a
  checklist that tells you to disable TLS verification).
- A helper script in `skills/*/scripts/` can be abused, for example through
  command injection or unsafe file handling.
- A real secret, token, or internal hostname slipped into an example.

## Supported versions

Only the latest release gets fixes.

| Version | Supported |
|---|---|
| Latest `0.x` release | Yes |
| Older releases | No |

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report privately through GitHub: go to the **Security** tab of this repo and
click **Report a vulnerability**. Include:

- The skill or file affected
- What the problem is and how it could be exploited
- A suggested fix, if you have one

## What to expect

- Acknowledgement within 3 business days
- A first assessment within 7 business days
- A fix or a decision within 30 days, depending on severity

If you found a leaked credential, say so in the first line of the report so it
can be revoked first. You will be credited in the release notes unless you ask
not to be.
