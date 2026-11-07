---
name: privacy-review
description: Review a feature, design or codebase for privacy: build a data inventory (fields, purpose, lawful basis, storage, access, retention, processors), trace personal data through models, schemas, logs, analytics, error trackers and LLM prompts, and check minimization, deletion, consent, data subject requests, cross-border transfers and DPIA triggers against GDPR and CCPA/CPRA. Use when the user asks for a privacy review or data inventory, a PR adds or changes personal data fields, tracking SDKs or third-party processors, or someone asks about right to erasure, consent, DSARs, data residency or whether a DPIA is needed.
---

# Privacy Review

Find out what personal data a feature touches, where it goes, and whether you can delete it when asked. Most privacy problems are engineering problems: a field nobody needed, a copy in a search index the delete job forgot, an analytics SDK that loads before the user says yes.

This skill maps findings to GDPR and CCPA/CPRA so the team knows which rule is in play. It is not legal advice. When a finding depends on legal interpretation, say so and name who should decide (legal, the DPO, or the privacy team).

## When to use

- A design doc or ticket introduces new personal data: sign-up fields, location, health, payment, biometrics, children's data, uploaded documents.
- A PR adds a column, model field, event property, tracking pixel, analytics or session replay SDK, or a new vendor integration.
- Someone asks for a data inventory, a record of processing (RoPA), or "where do we store user emails?".
- A user or regulator request lands: access, export, correction, deletion, opt-out of sale or sharing.
- The team plans to send data to a new region, a new cloud provider, or an LLM API.
- Someone asks "do we need a DPIA for this?".

Not for: scrubbing PII from logs, metrics and traces in detail (use `observability-setup`, though flag obvious leaks here), security threats such as IDOR or SSRF (use `threat-modeling`), hardcoded keys and rotation (use `secrets-management`), or prompt injection and model data leakage controls (use `llm-app-security`).

## Steps

1. Scope it. One paragraph: what the feature does, whose data it handles (customers, employees, minors, end users of your customers), and which regions they live in. Note whether you are the controller or a processor for this data, since that changes who answers DSARs.
2. Build the inventory. For every personal data field, record source, purpose, lawful basis, storage location, who can access it, retention, and which processors receive it. Use the inventory table in the output format.
3. Trace the flows in code. Search for each field and follow it:
   - Models and schemas: `grep -rniE "email|phone|ssn|dob|birth|address|ip_addr|lat|lng|passport|tax_id" --include=*.py --include=*.ts --include=*.sql --include=*.prisma .`
   - Logs and error trackers: logger calls with request bodies or user objects, Sentry `setUser`, `before_send` hooks.
   - Analytics: `identify`, `track`, `gtag`, `posthog.capture`, Segment `traits`, session replay config.
   - LLM prompts: user records or free text sent to a model API, prompt logging, vendor retention settings.
   - Copies: caches, search indexes, data warehouse syncs, CSV exports, backups, queues and dead-letter queues.
4. Check minimization. For each field ask: what breaks if we drop it? Can we store less (year instead of full birth date, city instead of street, a hash instead of the value)?
5. Check retention and deletion. Find the TTL job, cron or lifecycle rule for each store. Then walk a delete request end to end: primary DB, replicas, caches, search index, warehouse, object storage, backups, and every processor.
6. Check consent and opt-out. Non-essential cookies and tracking SDKs must not load or fire until consent is given where consent is the basis. Honor withdrawal, and honor the Global Privacy Control (GPC) signal for CCPA/CPRA opt-out of sale or sharing.
7. Check data subject requests. Can you find all data for one person by a stable ID? Is there an export in a machine-readable format? Is the requester verified before data is released?
8. Check transfers and residency. List where each store and processor runs. Transfers out of the EEA or UK need a mechanism (adequacy, EU-US Data Privacy Framework, SCCs). Flag any contractual residency promises the design would break.
9. Check protection of sensitive fields. Encryption at rest and in transit, field-level encryption or tokenization for special category data and government IDs, pseudonymous IDs in analytics, access limited by role and audited.
10. Decide on a DPIA. Use the triggers in the checklist. If any apply, recommend one and name the DPO or privacy lead as the owner. Do not decide on the team's behalf that a DPIA is not needed when triggers are borderline.
11. Write the report using the output format. Mark which findings need legal or DPO input.

## Checklist

Inventory and records (GDPR Art. 30):

- Every personal data field has a named purpose and a lawful basis (Art. 6: consent, contract, legal obligation, vital interests, public task, legitimate interests).
- Special category data (health, biometrics, religion, sexual orientation, union membership) also needs an Art. 9 condition. Flag it for legal.
- Processors are listed with a signed DPA and their sub-processors are known.

Principles (Art. 5) and privacy by design (Art. 25):

- Purpose limitation: data collected for billing is not reused for ad targeting without a new basis.
- Minimization: no "might be useful later" fields. Optional fields are optional in the API, not only in the UI.
- Defaults are private: profile visibility, marketing opt-ins and data sharing start off.
- Accuracy: users can correct their data.
- Storage limitation: each store has a retention period and something that enforces it.

Retention and erasure (Art. 17, CCPA right to delete):

- A delete path covers primary DB, read replicas, Redis, Elasticsearch or OpenSearch, warehouse tables, S3 objects, and processors via their deletion APIs.
- Soft delete (`deleted_at`) is followed by a hard delete or anonymization job within a set window.
- Backups age out on a documented schedule, and restore procedures re-apply pending deletions.
- Legal holds and statutory retention (tax, accounting) are explicit exceptions, not silent ones.

Consent and tracking:

- Tag managers and SDKs (Google Analytics, Meta Pixel, Hotjar, session replay) load only after consent where required.
- Consent records store version, timestamp and choices, and withdrawal is as easy as giving consent.
- "Do Not Sell or Share My Personal Information" link and GPC handling where CCPA/CPRA applies.
- Session replay masks inputs by default.

Data subject requests:

- Access and export return all stores, not only the main users table.
- Response deadlines are tracked: GDPR one month (extendable by two), CCPA/CPRA 45 days (extendable by 45).
- Identity is verified before export or delete, and the request is logged.

Third parties and LLMs:

- Only the fields a vendor needs are sent (no full user object to an email or support tool).
- Error trackers scrub request bodies, cookies and headers, and send a pseudonymous user ID.
- LLM calls strip or pseudonymize personal data where possible, and the vendor's retention and training settings are known.

Security of processing (Art. 32):

- TLS everywhere, encryption at rest, field-level encryption or tokenization for government IDs, financial and health data.
- Pseudonymous IDs for analytics and the mapping table access-controlled.
- Access to personal data is role-based, least privilege, and audited.

DPIA triggers (Art. 35), recommend one if any apply:

- Large-scale processing of special category data or data about minors.
- Systematic monitoring: location tracking, behavioral profiling, employee monitoring.
- Automated decisions with legal or similar effects (credit, hiring, account bans).
- New technology applied to personal data, including LLM features over user content.
- Combining datasets from different sources in ways users would not expect.

See [references/regulation-map.md](references/regulation-map.md) for the GDPR article and CCPA/CPRA mapping and when to involve legal or the DPO.

## Output format

Data inventory:

| Field | Source | Purpose | Lawful basis | Stored in | Access | Retention | Processors | Region |
|---|---|---|---|---|---|---|---|---|
| `users.email` | Sign-up form | Login, receipts | Contract | Postgres `users`, Redis session | Support (read), app | Account life + 30 days | Postmark, Zendesk | eu-west-1, US (Zendesk) |
| `users.birth_date` | Sign-up form | Age check | Legal obligation | Postgres `users` | App | Account life | None | eu-west-1 |

Findings:

| Severity | Area | Location | Issue | Regulation | Fix | Legal/DPO? |
|---|---|---|---|---|---|---|
| High | Erasure | `jobs/delete_user.py:22` | Delete job skips the OpenSearch `users` index and the warehouse sync | GDPR Art. 17, CCPA delete | Add index delete and warehouse tombstone, add a test that searches for the user after deletion | No |
| High | Consent | `web/src/main.tsx:8` | Meta Pixel loads before the cookie banner choice | GDPR Art. 6, ePrivacy | Load the pixel from the consent callback only | No |
| Medium | Minimization | `models/user.py:14` | Full birth date stored, only used for an 18+ check | GDPR Art. 5(1)(c) | Store `is_adult` and the check date | Confirm with legal if age proof must be kept |

After the tables:

1. A Mermaid flow of personal data across stores and processors if there are more than three hops.
2. DPIA recommendation: needed, not needed, or ask the DPO, with the triggers that apply.
3. Open questions for legal or the DPO, stated as specific questions.

Severity: Critical (personal data public or sent to an unknown third party, no way to delete), High (erasure gaps, tracking without consent, special category data unencrypted), Medium (over-collection, no retention job, missing DPA), Low (documentation and inventory gaps).

## Examples

Bad: full user object sent to the error tracker and an LLM, analytics fires before consent, soft delete only.

```python
sentry_sdk.set_user({"email": user.email, "ip_address": request.remote_addr})
analytics.identify(user.email, {"name": user.full_name, "phone": user.phone})

summary = llm.complete(f"Summarize this support ticket for {user.full_name} "
                       f"({user.email}, {user.address}): {ticket.body}")

def delete_user(user_id):
    User.objects.filter(id=user_id).update(deleted_at=now())
```

Good: pseudonymous IDs, consent gate, minimal prompt, full erasure path.

```python
sentry_sdk.set_user({"id": user.public_id})  # random UUID, not the DB key or email

if consent.allows(user, "analytics"):
    analytics.identify(user.public_id, {"plan": user.plan})

summary = llm.complete(f"Summarize this support ticket: {redact_pii(ticket.body)}")

def delete_user(user_id):
    user = User.objects.get(id=user_id)
    search.delete(index="users", id=user.public_id)
    cache.delete_pattern(f"user:{user.public_id}:*")
    storage.delete_prefix(f"uploads/{user.public_id}/")
    for vendor in PROCESSORS:  # Postmark, Zendesk, analytics
        vendor.request_deletion(user.public_id)
    warehouse.tombstone("users", user.public_id)
    user.delete()  # replicas follow; backups expire in 35 days
    audit.log("user.erased", target=user.public_id)
```
