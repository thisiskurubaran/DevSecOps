# Doc templates

Copy the template, delete sections that do not apply, and fill the rest from the code. Empty sections are worse than no section.

## README

````markdown
# <project-name>

<One or two sentences: what it does and for whom.>

## Requirements
- <Runtime and version, e.g. Node 20+>
- <Services, e.g. Postgres 15, Redis 7>

## Quick start
```sh
git clone https://github.com/<org>/<project-name>.git
cd <project-name>
cp .env.example .env
<install command>
<run command>
```

## Configuration
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | none | Postgres connection string |
| `LOG_LEVEL` | no | `info` | `debug`, `info`, `warn`, `error` |

## Usage
<One real example with output.>

## Development
```sh
<test command>
<lint command>
```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License
<License name>. See [LICENSE](LICENSE).
````

## ADR (based on Michael Nygard's format)

```markdown
# ADR-<NNNN>: <Decision in a short phrase>

- Status: Proposed | Accepted | Deprecated | Superseded by ADR-<NNNN>
- Date: <YYYY-MM-DD>
- Deciders: <roles or handles>

## Context
<The problem, the constraints, and the forces at play. Facts and numbers.>

## Options considered
1. <Option A>: <pros>, <cons>
2. <Option B>: <pros>, <cons>
3. <Do nothing>: <pros>, <cons>

## Decision
We will <decision>.

## Consequences
- <What gets easier>
- <What gets harder, new costs, new risks>
- <Security or operational impact>
- <Follow-up work>
```

Tools: `adr-tools` (`adr new "Use Postgres for queues"`), `log4brains`.

## CHANGELOG (Keep a Changelog 1.1.0)

```markdown
# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.2.0] - 2026-03-14
### Added
- `--dry-run` flag for `orbit sync` (#388).

[Unreleased]: https://github.com/<org>/<repo>/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/<org>/<repo>/compare/v1.1.0...v1.2.0
```

## Docstring styles

Python, Google style:

```python
def fetch_user(user_id: str) -> User:
    """Load a user by ID.

    Args:
        user_id: UUID string.

    Returns:
        The User.

    Raises:
        UserNotFound: If no user has that ID.
    """
```

TypeScript, TSDoc:

```ts
/**
 * Load a user by ID.
 * @param userId - UUID string.
 * @returns The user, or `null` if not found.
 * @throws {@link DbError} If the database is unreachable.
 */
export async function fetchUser(userId: string): Promise<User | null> {}
```

Go:

```go
// FetchUser loads a user by ID. It returns ErrNotFound if no user matches.
// It is safe for concurrent use.
func FetchUser(ctx context.Context, id string) (*User, error)
```

Java, Javadoc:

```java
/**
 * Loads a user by ID.
 *
 * @param userId UUID string, not null
 * @return the user
 * @throws UserNotFoundException if no user has that ID
 */
public User fetchUser(String userId) { ... }
```
