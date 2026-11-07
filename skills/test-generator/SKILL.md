---
name: test-generator
description: Write unit and integration tests for existing code, covering the happy path, edge cases, error paths and boundary values, using the project's own test framework and style. Use when the user asks to add tests, raise coverage, write test cases for a function, module or endpoint, or test a bug fix.
---

# Test Generator

Write tests that would catch a real regression. Match the framework, layout and helpers the project already uses. Every test asserts something specific.

## When to use

- "Write tests for this function / class / endpoint."
- "Coverage on `src/billing` is 40 percent, bring it up."
- "Add integration tests for the orders API against a real database."
- New code was written without tests.

Not for: chasing down a failing bug first (use `debugging-playbook`, which ends with a regression test), scaffolding a new endpoint with tests (use `api-scaffolder`), or load and performance tests (use `performance-review`).

## Steps

1. Find the test setup. Look for:
   - Python: `pytest.ini`, `pyproject.toml [tool.pytest.ini_options]`, `conftest.py`, `tox.ini`.
   - JS/TS: `jest.config.*`, `vitest.config.*`, `"test"` script in `package.json`.
   - Go: `*_test.go` next to the code, `testdata/` folders.
   - Java: `src/test/java`, JUnit 5 in `pom.xml` or `build.gradle`.
2. Read two or three existing tests near the target code. Copy their naming, fixtures, factories and assertion style. Reuse existing fixtures in `conftest.py` or test helpers instead of writing new ones.
3. Read the code under test. List its inputs, outputs, side effects (DB, network, files, clock, randomness) and every branch.
4. Write a test plan before code. One line per case:
   - Happy path with typical input.
   - Boundaries: 0, 1, max, max+1, empty string, empty list.
   - Invalid input: wrong type, missing field, malformed format.
   - Error paths: dependency raises, times out, returns empty.
   - Security relevant input where it applies: path traversal (`../../etc/passwd`), SQL meta characters (`' OR 1=1 --`), oversized payloads, unicode.
   - State: called twice, concurrent calls, after a failure.
5. Decide unit or integration per case:
   - Unit: pure logic, mock only the boundary (HTTP client, clock, queue).
   - Integration: real DB or service in a container (Testcontainers, `docker compose`), real HTTP through the app's test client.
6. Write the tests. One behavior per test. Arrange, act, assert, with a blank line between each part.
7. Run them. Fix failures caused by the test. If a test fails because the code is wrong, stop and report it as a finding; do not change the assertion to match the bug.
8. Check the tests can fail. Break the code on purpose (flip a condition) and confirm at least one test goes red. For larger suites, run mutation testing: `mutmut run`, `npx stryker run`, or `go-mutesting`.
9. Report coverage for the target: `pytest --cov=<pkg> --cov-report=term-missing`, `vitest run --coverage`, `go test -cover ./...`.

## Checklist

- Test names state the behavior: `test_refund_rejects_amount_above_original_charge`, not `test_refund_2`.
- No logic in tests (no loops or ifs computing the expected value). Use `@pytest.mark.parametrize`, `it.each`, or Go table tests.
- No real network. Use `responses` or `respx` (Python), `msw` or `nock` (JS), `httptest.Server` (Go).
- No real clock. Freeze time with `freezegun` or `time-machine`, `vi.useFakeTimers()`, or inject a clock interface.
- Random values are seeded or injected.
- No `sleep` to wait for async work. Await the result, poll with a timeout, or use the framework's async support (`pytest-asyncio`, `async` tests in Jest).
- Each test sets up its own data and cleans up (transaction rollback, `tmp_path`, `t.TempDir()`).
- Tests pass in any order. Check with `pytest -p randomly` or `jest --randomize`.
- Mocks are checked (`assert_called_once_with`, `toHaveBeenCalledWith`) only when the call itself is the behavior.
- Assertions are specific: exact value, exact exception type and message, not `assert result` or `toBeTruthy()`.
- Fixtures use fake data only: `user@example.com`, `AKIAEXAMPLEEXAMPLE00`, `4111 1111 1111 1111` style test cards.
- Integration tests are marked so CI can split them (`@pytest.mark.integration`, Go build tag `//go:build integration`).

## Output format

1. Test plan table:

| # | Case | Type | Input | Expected |
|---|---|---|---|---|
| 1 | Valid refund | unit | amount=50, charge=100 | returns Refund(amount=50) |
| 2 | Refund above charge | unit | amount=150, charge=100 | raises RefundTooLarge |

2. The test file(s), with the path where each goes.
3. Command to run them and the result.
4. Coverage before and after for the target module, if measured.
5. Any bugs found, listed separately with file and line.

## Examples

Bad test (asserts nothing useful, hits the network, depends on the clock):

```python
def test_invoice():
    inv = create_invoice("cust_1", 100)
    assert inv
    time.sleep(2)
    r = requests.get("https://api.example.com/invoices/" + inv.id)
    assert r.status_code
```

Good tests:

```python
import pytest
from freezegun import freeze_time

from billing.invoices import create_invoice, InvalidAmount


@freeze_time("2026-01-15")
def test_create_invoice_sets_due_date_30_days_out():
    inv = create_invoice(customer_id="cust_1", amount_cents=10_000)

    assert inv.due_date.isoformat() == "2026-02-14"


@pytest.mark.parametrize("amount", [0, -1, -10_000])
def test_create_invoice_rejects_non_positive_amount(amount):
    with pytest.raises(InvalidAmount, match="must be positive"):
        create_invoice(customer_id="cust_1", amount_cents=amount)
```

Go table test:

```go
func TestParsePort(t *testing.T) {
    tests := []struct {
        name    string
        in      string
        want    int
        wantErr bool
    }{
        {"typical", "8080", 8080, false},
        {"lowest", "1", 1, false},
        {"highest", "65535", 65535, false},
        {"zero", "0", 0, true},
        {"above max", "65536", 0, true},
        {"not a number", "http", 0, true},
        {"empty", "", 0, true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParsePort(tt.in)
            if (err != nil) != tt.wantErr {
                t.Fatalf("ParsePort(%q) err = %v, wantErr %v", tt.in, err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("ParsePort(%q) = %d, want %d", tt.in, got, tt.want)
            }
        })
    }
}
```
