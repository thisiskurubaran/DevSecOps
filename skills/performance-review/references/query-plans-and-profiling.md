# Query plans and profiling

## Reading a Postgres plan

Always use `EXPLAIN (ANALYZE, BUFFERS)` on a copy of production-sized data. Plans on a 100-row dev table are meaningless. `ANALYZE` runs the query, so wrap writes in `BEGIN; ... ROLLBACK;`.

| Signal in the plan | Meaning | Usual fix |
|---|---|---|
| `Seq Scan` on a big table with a selective filter | no usable index | add an index on the filter columns |
| `Rows Removed by Filter` much higher than `rows` | index used for part of the filter only | composite index, or reorder columns |
| `Nested Loop` with `loops=` in the thousands | join driving many index lookups | check join order, statistics, maybe hash join with better estimates |
| estimated `rows` far from actual | stale statistics | `ANALYZE table;`, raise `default_statistics_target` for that column |
| `Sort Method: external merge Disk` | sort spilled | index matching `ORDER BY`, or raise `work_mem` for that query |
| `Buffers: shared read` high | data not in cache, disk reads | smaller rows, covering index (`INCLUDE`), more memory |
| `Index Scan` then `Heap Fetches` high on an index-only plan | visibility map not current | `VACUUM` the table |

Find the worst queries overall:

```sql
SELECT calls, round(mean_exec_time::numeric, 1) AS mean_ms,
       round(total_exec_time::numeric) AS total_ms, left(query, 100)
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

Unused indexes:

```sql
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

## MySQL

- `EXPLAIN ANALYZE` (8.0.18+) or `EXPLAIN FORMAT=TREE`.
- `type: ALL` means full table scan. `Using filesort` and `Using temporary` on large row counts are red flags.
- Slow query log: `slow_query_log=1`, `long_query_time=0.5`, then `pt-query-digest`.

## Profilers by runtime

| Runtime | CPU | Memory |
|---|---|---|
| Python | `py-spy record -o out.svg --pid <pid>`, `scalene`, `cProfile` + `snakeviz` | `tracemalloc`, `memray run`, `objgraph` |
| Node.js | `node --cpu-prof`, `clinic flame`, `0x` | `node --inspect` heap snapshots, `clinic heapprofiler` |
| Go | `net/http/pprof`, `go tool pprof -http=:8080 cpu.out` | `pprof -inuse_space`, `-alloc_space` |
| JVM | `async-profiler`, JFR (`-XX:StartFlightRecording`) | heap dump + Eclipse MAT, JFR allocation events |
| Ruby | `stackprof`, `rbspy` | `memory_profiler`, `derailed_benchmarks` |
| Browser | Chrome Performance tab, Lighthouse | Memory tab, 3-snapshot technique |

## Finding a memory leak

1. Warm up the process, then take heap snapshot A.
2. Run the suspect action many times (for example 500 requests).
3. Force GC if possible, take snapshot B.
4. Repeat the action, take snapshot C.
5. Objects that grow from A to B to C and are retained by a long-lived root (global map, cache, event emitter) are the leak.

## Benchmarks

- Micro: `pytest-benchmark`, `go test -bench . -benchmem`, `tinybench` / `vitest bench`, JMH.
- Load: `k6`, `wrk`, `vegeta`, `locust`. Report p50, p95, p99 and error rate, not only the mean.
- Run before and after on the same machine and data. Repeat at least 3 times.
