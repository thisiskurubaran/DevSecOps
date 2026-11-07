---
name: migration-helper
description: Write safe database schema and data migrations with rollback steps, lock and timeout checks, and an expand-and-contract plan for zero-downtime deploys. Use when the user asks to add, rename or drop a column or table, add an index or constraint, backfill data, or review a migration file for Postgres or MySQL in Alembic, Django, Rails, Flyway, Liquibase, Prisma, Knex, golang-migrate or plain SQL.
---

# Migration Helper

## When to use

- The user needs a schema change: new column, rename, type change, new index, foreign key, NOT NULL, drop.
- A data backfill or transform has to run against a live table.
- A migration file is in a PR and someone asks "is this safe to run in prod?"

Not for: slow queries and missing indexes found at runtime (use `performance-review`), release sequencing and feature flags across services (use `release-checklist`), or IaC for the database instance itself (use `iac-review`).

## Steps

1. Identify the engine, version and migration tool. Postgres 11+ and MySQL 8 behave differently on `ADD COLUMN ... DEFAULT`. Check `alembic.ini`, `db/migrate/`, `flyway.conf`, `prisma/schema.prisma`, `migrations/` folders.
2. Ask for or estimate table size and write traffic. A `CREATE INDEX` on 2k rows is fine. On 200M rows it needs `CONCURRENTLY` and a plan.
3. Classify each statement by the lock it takes (see [references/lock-matrix.md](references/lock-matrix.md)). Anything that takes `ACCESS EXCLUSIVE` on a hot table needs a safer form or a maintenance window.
4. Split breaking changes into expand and contract phases. Each phase ships in its own deploy:
   - Expand: add the new column or table, nullable, no default rewrite.
   - Migrate: dual write in app code, backfill in batches.
   - Switch: read from the new column.
   - Contract: drop the old column in a later release, after no code reads it.
5. Set timeouts at the top of the migration so a blocked lock fails fast instead of queueing every query behind it:
   - Postgres: `SET lock_timeout = '5s'; SET statement_timeout = '15min';`
   - MySQL: `SET SESSION lock_wait_timeout = 5;` and use `ALGORITHM=INPLACE, LOCK=NONE` where supported.
6. Write the down migration or a written rollback plan. If a step cannot be reversed (dropping data), say so and require a backup or snapshot first.
7. Keep schema changes and data backfills in separate migrations. Backfill in batches of 1k to 10k rows with a commit per batch and a short sleep.
8. Turn off the tool's wrapping transaction where needed (`CREATE INDEX CONCURRENTLY` cannot run in a transaction).
9. Run the migration up, down, and up again against a local copy. Run the linter if the project has one (`squawk`, `strong_migrations`, `django-migration-linter`, `atlas migrate lint`).
10. Report with the output format below.

## Checklist

Locking
- [ ] `lock_timeout` (Postgres) or `lock_wait_timeout` (MySQL) set before DDL.
- [ ] Indexes on large Postgres tables use `CREATE INDEX CONCURRENTLY` and `DROP INDEX CONCURRENTLY`.
- [ ] Foreign keys added as `NOT VALID`, then `VALIDATE CONSTRAINT` in a separate step.
- [ ] `NOT NULL` on a big Postgres table done via `CHECK (col IS NOT NULL) NOT VALID`, validate, then `SET NOT NULL` (Postgres 12+ skips the scan when a valid check exists).
- [ ] No column type change that rewrites the table (`int` to `bigint`, `varchar(50)` to `int`) on a hot table without a new-column plan.
- [ ] MySQL large table changes use `gh-ost` or `pt-online-schema-change` if `INSTANT` or `INPLACE` is not available.

Compatibility
- [ ] Old app version still works after the migration runs (deploy order: migrate, then roll out code).
- [ ] No rename or drop of a column that the currently deployed code reads.
- [ ] New columns are nullable or have a constant default (Postgres 11+ stores constant defaults without a rewrite).
- [ ] Enum changes: adding a value is fine, removing or renaming one is a contract-phase change.

Rollback and data
- [ ] Down migration exists and was run locally, or rollback is written out as manual steps.
- [ ] Destructive steps (`DROP COLUMN`, `DROP TABLE`, `TRUNCATE`) are in their own migration with a backup note.
- [ ] Backfill is batched, idempotent (`WHERE new_col IS NULL`), and resumable.
- [ ] No PII copied into new tables without the same access controls.

Tool specifics
- [ ] Alembic: `op.create_index(..., postgresql_concurrently=True)` inside `with op.get_context().autocommit_block():`.
- [ ] Django: `AddIndexConcurrently` from `django.contrib.postgres.operations` and `atomic = False` on the migration.
- [ ] Rails: `disable_ddl_transaction!` and `algorithm: :concurrently`, checked with `strong_migrations`.
- [ ] Prisma: review the generated SQL in `migration.sql` before `prisma migrate deploy`. Prisma does not add `CONCURRENTLY` for you.

## Output format

```markdown
### Migration plan: <short name>

Engine: Postgres 15 | Tool: Alembic | Table size: ~40M rows

| Phase | Deploy | Migration | Lock | Reversible |
|---|---|---|---|---|
| expand | 1 | add `orders.customer_ref` nullable | brief ACCESS EXCLUSIVE (metadata only) | yes |
| backfill | 1 | batch update 5k rows/commit | ROW EXCLUSIVE per batch | yes (set NULL) |
| switch | 2 | app reads `customer_ref` | none | yes (flag) |
| contract | 3 | drop `orders.customer_id_legacy` | brief ACCESS EXCLUSIVE | no, needs snapshot |

### Risks
| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| high | migrations/0042_idx.py | 12 | `CREATE INDEX` without CONCURRENTLY on 40M rows | use `postgresql_concurrently=True` in autocommit block |

### Rollback
1. ...
```

## Examples

Bad: blocks writes on a large table and cannot roll back cleanly.

```sql
ALTER TABLE orders ADD COLUMN status text NOT NULL DEFAULT 'pending';
CREATE INDEX idx_orders_status ON orders (status);
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_id) REFERENCES customers (id);
```

Good: short locks, fail fast, validate separately.

```sql
-- migration 0042 (no wrapping transaction)
SET lock_timeout = '5s';
ALTER TABLE orders ADD COLUMN status text;            -- metadata only
CREATE INDEX CONCURRENTLY idx_orders_status ON orders (status);
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;

-- migration 0043
SET lock_timeout = '5s';
ALTER TABLE orders VALIDATE CONSTRAINT fk_customer;   -- SHARE UPDATE EXCLUSIVE, writes continue

-- down for 0042
DROP INDEX CONCURRENTLY IF EXISTS idx_orders_status;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_customer;
ALTER TABLE orders DROP COLUMN IF EXISTS status;
```

Bad: one-shot backfill that holds row locks on every row for minutes.

```python
op.execute("UPDATE orders SET status = 'pending'")
```

Good: batched and resumable, in its own migration.

```python
def upgrade():
    conn = op.get_bind()
    while True:
        n = conn.execute(sa.text("""
            UPDATE orders SET status = 'pending'
            WHERE id IN (SELECT id FROM orders WHERE status IS NULL LIMIT 5000)
        """)).rowcount
        if n == 0:
            break
```

A quick static check for risky SQL is in [scripts/lint_migration.py](scripts/lint_migration.py). Run it on a `.sql` file or the SQL your tool generates (`alembic upgrade head --sql`, `python manage.py sqlmigrate app 0042`).
