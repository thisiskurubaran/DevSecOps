---
name: performance-review
description: Review code and query plans for performance problems such as N+1 queries, missing or unused indexes, unbounded queries, unnecessary React re-renders, large bundles, blocking I/O and memory leaks, then rank findings by measured or likely impact. Use when the user says an endpoint, page or job is slow, asks for a performance or profiling review, shares an EXPLAIN plan, flame graph or heap snapshot, or wants a diff checked for performance regressions.
---

# Performance Review

## When to use

- "This endpoint takes 4 seconds", "the dashboard is janky", "memory keeps growing until the pod is OOMKilled".
- The user shares `EXPLAIN (ANALYZE, BUFFERS)` output, a flame graph, a Chrome Performance trace, a React Profiler export or a heap snapshot.
- A PR touches ORM queries, loops over collections, caching, or a hot React component and someone asks if it will be slow.

Not for: writing the index migration itself (use `migration-helper`), setting up tracing, metrics and SLO alerts (use `observability-setup`), or a general correctness review (use `code-review`).

## Steps

1. Get a number first. Ask for or find the current latency, p95/p99, query count, memory curve, or bundle size. Without a baseline you cannot show an improvement. If there is none, say how to get one (see the checklist tools) and continue with likely issues marked "unmeasured".
2. Find where time goes before reading code line by line:
   - Backend: traces (OpenTelemetry, Datadog APM), `py-spy record`, `pprof`, `clinic flame`, `async-profiler`, slow query log, `pg_stat_statements`.
   - Frontend: Lighthouse, Chrome Performance tab, React DevTools Profiler with "Highlight updates", `webpack-bundle-analyzer` or `vite-bundle-visualizer`.
3. Check the database layer. Most backend slowness is here.
   - Count queries per request. Look for the same query shape repeated N times.
   - Run `EXPLAIN (ANALYZE, BUFFERS)` on the slow query. Look for `Seq Scan` on large tables, `Rows Removed by Filter` much larger than rows returned, nested loops with high loop counts, and sorts spilling to disk.
   - Check that filter, join and sort columns have a matching index, in the right column order.
4. Check application code for work inside loops: queries, HTTP calls, regex compiles, JSON parsing, `await` in a `for` loop where calls could run in parallel.
5. Check for unbounded work: queries with no `LIMIT`, endpoints with no pagination, `SELECT *` of wide rows, loading whole files into memory.
6. Check memory: caches with no max size or TTL, listeners or intervals never removed, global maps keyed by request or user ID, closures holding large objects.
7. Check the frontend: components re-rendering on every parent render, new object or function props each render, context values that change on every render, large lists without virtualization, images without dimensions or lazy loading.
8. Rank findings by impact times how often the path runs. A 50 ms fix on a hot path beats a 2 s fix on a monthly admin report.
9. For each finding give a concrete fix and how to verify it (query count assertion, benchmark, before and after `EXPLAIN`).

## Checklist

Database
- [ ] No N+1: Django `select_related` / `prefetch_related`, Rails `includes` (and the `bullet` gem in dev), SQLAlchemy `selectinload` / `joinedload`, Prisma `include`, GORM `Preload`, Hibernate `JOIN FETCH` or `@EntityGraph`.
- [ ] Query count asserted in tests on hot endpoints: `django_assert_num_queries`, `assertNumQueries`, `n_plus_one_control`.
- [ ] Indexes match `WHERE`, `JOIN` and `ORDER BY` columns. Composite index leading column is the most selective equality filter.
- [ ] Unused indexes found via `pg_stat_user_indexes` (`idx_scan = 0`) or `sys.schema_unused_indexes` in MySQL. They slow writes.
- [ ] No functions on indexed columns in filters (`WHERE lower(email) = ?` needs an expression index).
- [ ] Offset pagination on large tables replaced with keyset (`WHERE id > ? ORDER BY id LIMIT 50`).
- [ ] Connection pool sized for the worker count (PgBouncer, HikariCP `maximumPoolSize`).

Application
- [ ] No I/O inside loops that could be batched (`WHERE id IN (...)`, bulk APIs, `Promise.all` with a concurrency cap via `p-limit`).
- [ ] No blocking calls on an event loop (`fs.readFileSync` in a request handler, `requests` in an `async def` FastAPI route, `time.sleep` in asyncio).
- [ ] Caches have a max size and TTL (`lru-cache` `max`, `functools.lru_cache(maxsize=...)`, Caffeine `maximumSize`, Redis `EXPIRE`).
- [ ] Large responses streamed or paginated, gzip or brotli enabled.
- [ ] Serialization does not trigger lazy loads (DRF serializers, Jackson on JPA entities).

Memory
- [ ] Event listeners, `setInterval`, subscriptions and observers cleaned up (`useEffect` cleanup, `removeEventListener`, `unsubscribe`).
- [ ] No module-level maps that grow per request. Use `WeakMap` or a bounded cache.
- [ ] Heap compared across two snapshots under load (Chrome DevTools, `node --inspect`, `tracemalloc`, `memray`, `pprof -inuse_space`).

Frontend (React)
- [ ] Expensive children wrapped in `React.memo` only when props are stable. Callbacks with `useCallback`, derived values with `useMemo`, or the React Compiler if the project uses it.
- [ ] Context split so fast-changing values do not re-render the whole tree.
- [ ] Lists over a few hundred rows virtualized (`react-window`, `@tanstack/react-virtual`).
- [ ] Route-level code splitting (`React.lazy`, `next/dynamic`). No full `lodash` or `moment` import.
- [ ] Core Web Vitals checked: LCP under 2.5 s, INP under 200 ms, CLS under 0.1.

More detail on reading plans and profiles: [references/query-plans-and-profiling.md](references/query-plans-and-profiling.md).

## Output format

```markdown
### Performance review: GET /api/orders

Baseline: p95 1.8 s, 203 queries per request (from OpenTelemetry trace, staging).

| Severity | File | Line | Issue | Fix | Verify |
|---|---|---|---|---|---|
| high | api/views/orders.py | 41 | N+1: `order.customer` loaded per row (200 queries) | `.select_related("customer")` | `django_assert_num_queries(3)` |
| high | db: orders | - | `Seq Scan` on 12M rows filtering `tenant_id, created_at` | index `(tenant_id, created_at DESC)` via migration-helper | `EXPLAIN ANALYZE` shows Index Scan |
| medium | api/views/orders.py | 18 | no `LIMIT`, returns all orders | keyset pagination, max 100 | response size |
| low | web/OrderRow.tsx | 12 | inline `onClick` breaks `React.memo` | `useCallback` | Profiler render count |

Expected result: p95 under 200 ms, 3 queries per request. Re-measure after each fix.
```

Severity: high means user-facing latency, errors or OOM on a hot path. Medium means measurable cost on a warm path or a risk that grows with data. Low means minor or rare.

## Examples

Bad: N+1 in Django, one query per order for the customer.

```python
orders = Order.objects.filter(tenant=tenant)[:100]
return [{"id": o.id, "customer": o.customer.name} for o in orders]   # 101 queries
```

Good: one join, query count pinned in a test.

```python
orders = Order.objects.filter(tenant=tenant).select_related("customer")[:100]
return [{"id": o.id, "customer": o.customer.name} for o in orders]   # 1 query

def test_orders_query_count(client, django_assert_num_queries):
    with django_assert_num_queries(3):   # session, user, orders
        client.get("/api/orders")
```

Bad: React effect leaks a listener and re-subscribes every render.

```tsx
function Price({ symbol }) {
  const [p, setP] = useState(0);
  useEffect(() => {
    feed.on("tick", (t) => t.symbol === symbol && setP(t.price));
  });                                   // no deps, no cleanup
  return <span>{p}</span>;
}
```

Good: stable subscription with cleanup.

```tsx
function Price({ symbol }) {
  const [p, setP] = useState(0);
  useEffect(() => {
    const onTick = (t) => t.symbol === symbol && setP(t.price);
    feed.on("tick", onTick);
    return () => feed.off("tick", onTick);
  }, [symbol]);
  return <span>{p}</span>;
}
```
