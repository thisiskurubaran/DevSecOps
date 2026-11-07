---
name: refactoring-guide
description: Plan and apply small, behavior-preserving refactors one step at a time, running tests after each step and adding characterization tests first when coverage is thin. Use when the user asks to refactor, clean up, simplify, split a large function or class, remove duplication, rename across a codebase, extract a module, or pay down tech debt without changing behavior.
---

# Refactoring Guide

## When to use

- "Refactor this", "clean this up", "this function is 400 lines, split it".
- Renaming or moving code across many files.
- Removing duplication, dead code, or a deprecated internal API.
- Preparing code so a feature or fix is easy to add next ("make the change easy, then make the easy change").

Not for: finding bugs or ranking review findings in a diff (use `code-review`), fixing a known bug (use `debugging-playbook`), speeding up slow code (use `performance-review`), or writing a test suite from scratch (use `test-generator`).

## Steps

1. State the goal in one sentence and what must not change: public API, output format, DB schema, log lines that alerts depend on, error messages clients parse.
2. Check the safety net. Run the existing tests and note the result. Check coverage for the code you will touch (`pytest --cov=pkg --cov-report=term-missing`, `npx jest --coverage --collectCoverageFrom=src/billing/**`, `go test -cover ./billing/...`).
3. If coverage on the target is thin, write characterization tests first. Pin current behavior, including odd cases, even if they look wrong. Snapshot or golden-file tests work well for big outputs. Commit them on their own.
4. Break the work into steps that each take a few minutes and leave the code compiling and green. Use named refactorings so the step is clear (see [references/refactoring-catalog.md](references/refactoring-catalog.md)).
5. Do one step. Run the fast tests. If red, revert that step (`git checkout -- <file>` or `git stash`) instead of debugging forward.
6. Prefer tool-driven changes over hand edits for renames and moves: IDE rename, `gopls rename`, `rope`, `jscodeshift`, `ts-morph`, `comby`, `semgrep --autofix`, OpenRewrite for Java. They catch references text search misses.
7. Keep behavior changes out. If you spot a bug, write it down and fix it in a separate change with its own test.
8. Keep each commit to one kind of change: a rename commit, a move commit, an extract commit. Reviewers can then skim the mechanical ones.
9. After the last step run the full suite, linters and type checker. Diff public signatures (`git diff main -- '*.d.ts'`, `api-extractor`, `go doc` output, `japicmp`) to confirm the API did not move unless intended.
10. Report the steps, test results, and anything you left for later.

## Checklist

Before
- [ ] Goal and invariants written down.
- [ ] Tests pass on the starting commit.
- [ ] Coverage on touched code checked. Characterization tests added where it is low.
- [ ] No unrelated uncommitted changes in the working tree.

During
- [ ] Each step compiles and passes tests.
- [ ] No mixed commits (refactor plus feature, or refactor plus bug fix).
- [ ] Renames done with a semantic tool, then grep for string references (config files, reflection, templates, SQL, logs).
- [ ] Deprecated paths kept as thin wrappers with a deprecation note if external callers exist, rather than deleted.
- [ ] No new dependencies added just for the refactor.

After
- [ ] Full test suite, lint (`eslint`, `ruff`, `golangci-lint`, `rubocop`) and type check (`tsc --noEmit`, `mypy`, `pyright`) pass.
- [ ] Public API diff is empty or intentional.
- [ ] Complexity went down, not sideways: check with `radon cc -s`, `gocyclo -over 15`, `eslint complexity` rule, or `lizard`.
- [ ] Dead code removed is truly unused: `vulture`, `ts-prune` / `knip`, `deadcode` for Go, `unused` in staticcheck.
- [ ] Security-relevant code (auth checks, input validation, escaping) still runs on every path it did before.

## Output format

```markdown
### Refactor: <goal>

Invariants: public `BillingService` API, invoice PDF output, `invoice.created` event shape.

| # | Step | Kind | Files | Tests |
|---|---|---|---|---|
| 1 | pin current invoice totals | characterization tests | tests/test_invoice_golden.py | 14 added, pass |
| 2 | extract `calculate_tax()` | extract function | billing/invoice.py | pass |
| 3 | replace tax `if` chain with lookup table | replace conditional | billing/tax.py | pass |
| 4 | move `Money` to `billing/money.py` | move | 6 files | pass |

Results: 212 tests pass, `mypy` clean, `radon cc` worst block went from F (42) to B (8).

Left for later:
- `apply_discount()` rounds half-down, looks like a bug. Not changed. Ticket suggested.
```

## Examples

Bad: one big rewrite that mixes cleanup with a behavior change and has no test pinning the old output.

```python
# before: 120-line process_order() with nested ifs
# after: new OrderPipeline class, new rounding rule, renamed fields in the
# returned dict, and "while I was here" a changed default currency
```

Good: small named steps, behavior pinned first.

```python
# step 1: characterization test
def test_process_order_totals_golden(snapshot):
    for case in load_cases("tests/data/orders.json"):
        assert process_order(case) == snapshot(name=case["id"])

# step 2: extract function, no logic change
def _line_total(item):
    return item["qty"] * item["unit_price"] - item.get("discount", 0)

def process_order(order):
    subtotal = sum(_line_total(i) for i in order["items"])
    ...
```

Bad: renaming with search and replace.

```sh
sed -i 's/getUser/fetchUser/g' $(git ls-files '*.ts')   # also hits getUserAgent, comments, strings
```

Good: semantic rename, then check for string references.

```ts
// rename.ts, run with: npx tsx rename.ts (or use the IDE rename action)
import { Project } from "ts-morph";
const project = new Project({ tsConfigFilePath: "tsconfig.json" });
project.getSourceFileOrThrow("src/users.ts").getFunctionOrThrow("getUser").rename("fetchUser");
await project.save();
```

```sh
git grep -nw "getUser"   # leftovers in config, docs, route strings, mocks
```

Bad: nested conditionals hide the main path.

```go
func Charge(u *User, amt int64) error {
	if u != nil {
		if u.Active {
			if amt > 0 {
				return gateway.Charge(u.ID, amt)
			}
			return ErrBadAmount
		}
		return ErrInactive
	}
	return ErrNoUser
}
```

Good: guard clauses, same errors in the same order, existing tests unchanged.

```go
func Charge(u *User, amt int64) error {
	if u == nil {
		return ErrNoUser
	}
	if !u.Active {
		return ErrInactive
	}
	if amt <= 0 {
		return ErrBadAmount
	}
	return gateway.Charge(u.ID, amt)
}
```
