# Test prompts for llm-app-security

How to test: copy `skills/llm-app-security` to `~/.claude/skills/`, start a fresh Claude Code session, and try each prompt below.

## Should trigger

1. "Review our support agent in `agent/`. It reads customer emails, searches a pgvector knowledge base shared by all tenants, and has tools to issue refunds and send replies. Is it safe against prompt injection?"
2. "Set up a promptfoo red team for our RAG chatbot at staging and tell me what to fix. The model's answer is rendered with `marked` into the page."

## Should not trigger

1. "Our OpenAI API key is hardcoded in `config.py` and was pushed to GitHub. How do we rotate it and move it to Vault?"
   This belongs to `secrets-management`.
