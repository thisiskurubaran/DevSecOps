# Test prompts for incident-response

How to test: copy `skills/incident-response` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Checkout has been throwing 502s for 10 minutes since the last deploy. What do we do right now?"
2. "Someone pushed an AWS access key to our public GitHub repo an hour ago. Walk me through containment."

## Should not trigger

1. "The outage is over. Help me write up a blameless timeline and action items from these Slack notes."
   This belongs to `incident-postmortem`.
