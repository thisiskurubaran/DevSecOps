# Lock matrix

What common DDL does to a live table. Check your exact version's docs before relying on this.

## Postgres

| Statement | Lock | Blocks reads | Blocks writes | Rewrites table | Safer form |
|---|---|---|---|---|---|
| `ADD COLUMN` nullable, no default | ACCESS EXCLUSIVE (brief) | briefly | briefly | no | fine with `lock_timeout` |
| `ADD COLUMN ... DEFAULT <constant>` (11+) | ACCESS EXCLUSIVE (brief) | briefly | briefly | no | fine on 11+ |
| `ADD COLUMN ... DEFAULT now()` or volatile | ACCESS EXCLUSIVE | yes | yes | yes | add nullable, backfill, then set default |
| `ALTER COLUMN TYPE` (most changes) | ACCESS EXCLUSIVE | yes | yes | yes | new column, dual write, backfill, swap |
| `ALTER COLUMN SET NOT NULL` | ACCESS EXCLUSIVE | yes | yes | no, but full scan | `CHECK ... NOT VALID`, `VALIDATE`, then `SET NOT NULL` (12+) |
| `CREATE INDEX` | SHARE | no | yes | no | `CREATE INDEX CONCURRENTLY` |
| `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | no | no | no | check for `INVALID` index if it fails, drop and retry |
| `ADD FOREIGN KEY` | SHARE ROW EXCLUSIVE on both tables | no | yes | no | `NOT VALID`, then `VALIDATE CONSTRAINT` |
| `VALIDATE CONSTRAINT` | SHARE UPDATE EXCLUSIVE | no | no | no | |
| `ADD UNIQUE` constraint | SHARE (index build) | no | yes | no | `CREATE UNIQUE INDEX CONCURRENTLY`, then `ADD CONSTRAINT ... USING INDEX` |
| `RENAME COLUMN` / `RENAME TABLE` | ACCESS EXCLUSIVE (brief) | briefly | briefly | no | breaks running code: expand and contract |
| `DROP COLUMN` | ACCESS EXCLUSIVE (brief) | briefly | briefly | no | only after code stops reading it |
| `VACUUM FULL`, `CLUSTER` | ACCESS EXCLUSIVE | yes | yes | yes | `pg_repack` |

Find blockers while a migration waits:

```sql
SELECT pid, wait_event_type, state, now() - query_start AS age, left(query, 80)
FROM pg_stat_activity
WHERE pid IN (SELECT unnest(pg_blocking_pids(<migration_pid>)));
```

## MySQL 8 (InnoDB)

| Statement | Best algorithm | Concurrent DML |
|---|---|---|
| `ADD COLUMN` (last position or any, 8.0.29+) | `INSTANT` | yes |
| `DROP COLUMN` (8.0.29+) | `INSTANT` | yes |
| `ADD INDEX` | `INPLACE, LOCK=NONE` | yes |
| `MODIFY COLUMN` type change | `COPY` | no |
| `ADD FOREIGN KEY` | `INPLACE` only with `foreign_key_checks=0` | yes |
| Change `NULL` to `NOT NULL` | `INPLACE` (rebuilds) | yes, slow |

State the algorithm explicitly so MySQL errors instead of silently falling back to `COPY`:

```sql
ALTER TABLE orders ADD COLUMN status VARCHAR(20), ALGORITHM=INSTANT;
ALTER TABLE orders ADD INDEX idx_status (status), ALGORITHM=INPLACE, LOCK=NONE;
```

For `COPY` changes on large tables use `gh-ost` or `pt-online-schema-change`.

## Linters

| Tool | Stack |
|---|---|
| `squawk` | Postgres SQL files |
| `strong_migrations` | Rails |
| `django-migration-linter` | Django |
| `atlas migrate lint` | any SQL, Postgres and MySQL |
