---
name: debugging-playbook
description: Debug a reported bug step by step. Reproduce it, isolate the cause with logs, bisection and minimal cases, apply the smallest fix, then add a regression test that fails before the fix. Use when the user reports an error, stack trace, failing test, crash, wrong output, flaky behavior or "it worked yesterday" regression.
---

# Debugging Playbook

Find the cause before touching the code. Prove the fix with a test that failed before it. Work in this order: reproduce, isolate, fix, guard.

## When to use

- The user pastes a stack trace, error message or failing CI log.
- "This returns the wrong value", "it crashes when...", "this test is flaky".
- "It worked last week and now it does not."
- A production error from Sentry, logs or traces needs a code fix.

Not for: writing tests for code that works (use `test-generator`), slow code with correct output (use `performance-review`), live outage coordination and comms (use `incident-response`), or the write-up afterward (use `incident-postmortem`).

## Steps

1. Collect the facts. Ask for what is missing:
   - Exact error text and full stack trace.
   - Expected result vs actual result.
   - Input, environment, version or commit SHA, and when it started.
   - How often: always, sometimes, only in one environment.
2. Reproduce it locally or in a test. Write the smallest command or test that shows the bug:
   - A failing unit test is best. A `curl` against a local server or a short script is fine.
   - If you cannot reproduce it, compare environments: versions (`pip freeze`, `npm ls`, `go version -m`), config, env vars, data, time zone, locale, CPU arch.
   - Do not move on until you have a repro or a clear reason why you cannot get one.
3. Read the stack trace from the bottom frame in your code, not the library frame. Open that line and its callers.
4. Form one hypothesis at a time and test it. Write it down: "the cache returns a stale user because the key ignores tenant_id". Then check it with a log line, a debugger breakpoint or an assertion.
5. Narrow it down with the cheapest tool that works:
   - Regression with a known good commit: `git bisect start; git bisect bad; git bisect good <sha>; git bisect run <test-command>`.
   - Large input: cut it in half until the smallest failing input remains.
   - Many moving parts: remove or stub one dependency at a time.
   - Distributed systems: follow one request by trace ID through OpenTelemetry traces or logs.
   - Debuggers: `python -m pdb` or `breakpoint()`, `node --inspect`, `dlv debug`, `gdb`.
6. Confirm the root cause. You should be able to say why the bug happens and why it did not happen before. "Adding a retry made it go away" is not a root cause.
7. Write the regression test first. It must fail on the current code for the reason you found.
8. Apply the smallest fix that addresses the root cause. Avoid unrelated cleanup in the same change.
9. Run the regression test (now green) and the surrounding suite. For flaky bugs, loop the test: `pytest --count=200 -x` (pytest-repeat), `go test -count=500 -race -run TestX`, `npx jest --testNamePattern X` in a shell loop.
10. Remove temporary debug logging. Keep any log line that would have made this faster to find, at the right level and without personal data.
11. Check for the same bug elsewhere: `git grep` for the same pattern.
12. Report using the output format.

## Checklist

- Reproduced before fixing, or documented why not.
- Root cause stated in one or two sentences, with file and line.
- Regression test fails without the fix and passes with it.
- Fix is in the code that is wrong, not a workaround in the caller (unless the caller is wrong).
- No broad `try/except` or `catch` added to hide the symptom.
- No retry, sleep or timeout increase used as the fix unless the cause is a real transient failure.
- Flaky tests: checked for shared state, test order (`pytest -p randomly`), real clock, real network, unseeded randomness, and data races (`go test -race`, ThreadSanitizer).
- Debug output removed. No tokens, passwords or personal data left in logs.
- Same pattern searched for in the rest of the codebase.
- If the bug has a security angle (auth bypass, data leak, injection), flag it and hand off to `security-audit`.

Common causes worth checking early:

| Symptom | Usual suspects |
|---|---|
| Works locally, fails in CI | Missing env var, different tool version, time zone, file path case, test order |
| Fails only sometimes | Race condition, shared mutable state, unseeded random, clock, network |
| Wrong value after deploy | Stale cache, config drift, migration not run, feature flag state |
| Off by a day | UTC vs local time, DST change, date vs datetime |
| `None`/`undefined` error | Missing field in a new payload shape, optional value used without a check |
| Memory or handle growth | Unclosed files, connections or listeners, unbounded cache |

## Output format

```markdown
## Bug
<one sentence: what is wrong, for which input>

## Reproduction
<command or test name> -> <actual output>

## Root cause
<file:line> <why it happens, and why now if it is a regression>

## Fix
<summary of the change, diff or file list>

## Regression test
<test name and path>, fails before the fix: <failure message>, passes after.

## Checked
- Related suite: <command> : <result>
- Same pattern elsewhere: <none found / list>

## Follow-ups
<optional: monitoring, logging, or related bugs found>
```

## Examples

Bad (patch the symptom):

```python
def get_discount(user):
    try:
        return user.plan.discount
    except AttributeError:
        return 0  # sometimes plan is None??
```

Good (find why `plan` is None, fix it there, guard with a test):

```text
Root cause: accounts/signup.py:88 creates the User before the Plan row
commits, so users who sign up during a plan migration get plan=None.
Fix: create both inside one transaction.
```

```python
def test_signup_always_assigns_plan(db):
    user = signup(email="new@example.com", plan_code="basic")

    assert user.plan is not None
    assert user.plan.code == "basic"
```

Bad flaky-test fix:

```js
await new Promise(r => setTimeout(r, 2000)); // wait for the queue
expect(job.status).toBe("done");
```

Good:

```js
await waitFor(() => expect(getJob(job.id).status).toBe("done"), { timeout: 5000 });
```

Bisect a regression in one command:

```bash
git bisect start
git bisect bad HEAD
git bisect good v2.3.0
git bisect run pytest tests/test_discount.py -x -q
git bisect reset
```
