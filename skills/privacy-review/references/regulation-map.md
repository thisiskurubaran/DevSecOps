# Regulation map

A quick map from engineering checks to the rules behind them. This is a pointer for engineers, not legal advice. Exact obligations depend on the company's role (controller or processor), thresholds, and local law.

## GDPR articles

| Article | Topic | What engineers check |
|---|---|---|
| Art. 5 | Principles | Purpose limitation, minimization, accuracy, storage limitation, integrity and confidentiality |
| Art. 6 | Lawful basis | Each purpose has one basis. Consent is freely given, specific and withdrawable |
| Art. 9 | Special categories | Health, biometrics, genetics, religion, sexual orientation and similar need an extra condition |
| Art. 15, 20 | Access, portability | Export of all stores for one person in a machine-readable format (JSON, CSV) |
| Art. 16 | Rectification | Users or support can correct data, and corrections reach copies |
| Art. 17 | Erasure | Delete path covers replicas, caches, indexes, warehouse, backups, processors |
| Art. 21 | Objection | Opt-out of processing based on legitimate interests, including direct marketing |
| Art. 22 | Automated decisions | Human review path for decisions with legal or similar effects |
| Art. 25 | By design and default | Private defaults, minimal fields, pseudonymization built in |
| Art. 28 | Processors | Signed DPA, sub-processor list, deletion and return of data at contract end |
| Art. 30 | Records of processing | The data inventory, kept current |
| Art. 32 | Security of processing | Encryption, pseudonymization, access control, restore testing |
| Art. 33, 34 | Breach notification | Supervisory authority within 72 hours of awareness where required. Hand off to `incident-response` |
| Art. 35 | DPIA | Required for high-risk processing before it starts |
| Art. 44 to 49 | Transfers | Adequacy decision, EU-US Data Privacy Framework, SCCs, or a listed derogation |

## CCPA / CPRA basics

| Right or duty | What engineers check |
|---|---|
| Right to know and access | Export of categories and specific pieces of personal information |
| Right to delete | Same delete path as GDPR Art. 17, with service providers told to delete |
| Right to correct | Correction flow exists |
| Opt-out of sale or sharing | "Do Not Sell or Share" link, GPC signal honored, ad and cross-context tracking stops |
| Limit use of sensitive PI | Precise geolocation, government IDs, account credentials, health and similar limited to needed uses |
| Notice at collection | Categories and purposes shown before or at collection |
| Response time | 45 days, extendable once by 45 days with notice |
| Contracts | Service provider and contractor terms restrict use of the data |

Thresholds decide whether CCPA applies at all. Ask legal rather than guessing.

## When to involve legal or the DPO

- Choosing or changing a lawful basis, especially legitimate interests (needs a balancing test).
- Any special category data, children's data, or employee monitoring.
- A DPIA trigger applies or is borderline.
- A new country, region or vendor outside the EEA or UK receives personal data.
- A retention period is set by law (tax, health, financial records) or a legal hold applies.
- A DSAR is refused, partly fulfilled, or involves another person's data.
- Selling, sharing or combining datasets for advertising.
- A possible breach. Start `incident-response` and notify the DPO the same day.
