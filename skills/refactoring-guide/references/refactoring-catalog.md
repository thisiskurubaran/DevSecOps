# Refactoring catalog

Short list of named refactorings, when to use each, and the trap to watch for. Names follow Martin Fowler's catalog so they can be looked up.

| Refactoring | Use when | Watch for |
|---|---|---|
| Extract function | A block has a clear purpose and a comment explaining it | Captured variables that are mutated later; return them explicitly |
| Inline function | A wrapper adds nothing but indirection | Callers outside the repo; check with `git grep` and package consumers |
| Extract variable | A long expression is hard to read | Moving a call changes evaluation order or count (side effects) |
| Rename symbol | The name lies or is vague | Reflection, string lookups, serialized field names, DB column mappings, URL routes |
| Change function signature | Too many params, boolean flags | Keep the old signature as a deprecated wrapper for one release if public |
| Introduce parameter object | 4+ params travel together | Mutable shared objects; prefer immutable dataclass / record / readonly type |
| Replace conditional with polymorphism or lookup table | Long `if/elif` or `switch` on a type code | Default branch behavior; keep it |
| Decompose conditional | Complex boolean in an `if` | Short-circuit evaluation that guards a null access |
| Replace nested conditional with guard clauses | Arrow-shaped code | Early returns that skip cleanup; use `finally`, `defer`, `with` |
| Move function / move file | Code lives in the wrong module | Import cycles; run `madge --circular`, `pydeps`, `go vet` |
| Extract class / module | A class has two reasons to change | Shared private state; pass it in, do not reach back |
| Split loop | One loop does two jobs | Performance is rarely an issue; measure if it is hot |
| Replace temp with query | A temp variable hides a reusable calculation | Expensive or non-deterministic calls repeated |
| Remove dead code | Unused function, flag, branch | Dynamic dispatch, plugin registries, feature flags still on in some env |
| Replace magic number with constant | Literal with meaning (`86400`, `0.2`) | Same literal with different meanings; do not merge them |
| Encapsulate collection | Callers mutate an internal list | Return a copy or read-only view |
| Strangler fig | Replacing a whole subsystem | Run old and new side by side, compare outputs, cut over by flag |

## Codemod tools

| Language | Tools |
|---|---|
| TypeScript / JavaScript | IDE rename, `ts-morph`, `jscodeshift`, `knip` (dead code) |
| Python | IDE rename, `rope`, `libcst` codemods, `ruff --fix`, `vulture` |
| Go | `gopls rename`, `gofmt -r`, `eg`, `deadcode` |
| Java / Kotlin | IntelliJ refactor actions, OpenRewrite recipes |
| Any | `comby`, `semgrep --autofix`, `ast-grep` |

## Characterization test patterns

- Golden files: write current output to `testdata/*.golden`, compare on each run, regenerate only on purpose (`go test -update`, `pytest --snapshot-update`, `jest -u`).
- Approval tests: `approvaltests` libraries for Python, Java, .NET.
- Record and replay for HTTP: `vcrpy`, `polly.js`, `go-vcr`. Scrub tokens and cookies from cassettes before committing.
