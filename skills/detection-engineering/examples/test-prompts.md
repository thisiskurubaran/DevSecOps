# Test prompts for detection-engineering

How to test: copy `skills/detection-engineering` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Write a Sigma rule that alerts when someone stops CloudTrail logging in any of our AWS accounts, and convert it to Splunk SPL with sigma-cli."
2. "Our 'impossible travel' alert in Sentinel fires 200 times a week, mostly from people on the corporate VPN. How do I tune it without missing real account takeovers?"

## Should not trigger

1. "Falco keeps flagging a shell in our debug pods. How do I write an exception for that namespace?"
   This belongs to `runtime-security`.
