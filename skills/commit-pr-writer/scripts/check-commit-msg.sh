#!/bin/sh
# Check a commit message against Conventional Commits basics.
#
# Usage:
#   check-commit-msg.sh <file>        check a message file
#   echo "fix(api): x" | check-commit-msg.sh -
#
# As a git hook: copy to .git/hooks/commit-msg and make it executable.
# Exit code 0 when the message passes, 1 when it fails.

set -eu

if [ $# -ne 1 ]; then
  echo "usage: $0 <message-file|->" >&2
  exit 2
fi

if [ "$1" = "-" ]; then
  msg=$(cat)
else
  msg=$(cat "$1")
fi

# Ignore comment lines git adds to the editor buffer.
msg=$(printf '%s\n' "$msg" | grep -v '^#' || true)
summary=$(printf '%s\n' "$msg" | sed -n '1p')
second=$(printf '%s\n' "$msg" | sed -n '2p')
fail=0

types='feat|fix|docs|refactor|perf|test|build|ci|chore|revert'
if ! printf '%s\n' "$summary" | grep -Eq "^($types)(\([a-z0-9-]+\))?!?: .+"; then
  echo "FAIL: summary must look like 'type(scope): summary' with type in: $types" >&2
  fail=1
fi

len=$(printf '%s' "$summary" | wc -c | tr -d ' ')
if [ "$len" -gt 72 ]; then
  echo "FAIL: summary is $len chars, limit is 72" >&2
  fail=1
fi

case "$summary" in
  *.) echo "FAIL: summary ends with a period" >&2; fail=1 ;;
esac

if [ -n "$second" ]; then
  echo "FAIL: line 2 must be blank" >&2
  fail=1
fi

long=$(printf '%s\n' "$msg" | sed '1d' | awk 'length > 72 && !/^https?:\/\// { n++ } END { print n+0 }')
if [ "$long" -gt 0 ]; then
  echo "WARN: $long body line(s) over 72 chars" >&2
fi

if [ "$fail" -eq 0 ]; then
  echo "OK: $summary"
fi
exit "$fail"
