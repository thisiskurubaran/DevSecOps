# Test prompts for incident-postmortem

How to test: copy `skills/incident-postmortem` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Here is the Slack export from yesterday's checkout outage and the PagerDuty timeline. Write the postmortem."
2. "Review this RCA draft and tell me where it blames people or has vague action items."

## Should not trigger

1. "Our login page is down right now and the error rate is climbing. Help."
   This belongs to `incident-response`.
