# Workspace Agent

This repository now includes a lightweight local workspace agent.

## Quick start

```bash
python agent.py --prompt "Summarize this repository and point me to entry points."
```

Interactive mode:

```bash
python agent.py --interactive
```

## What it does

- reviews the workspace structure
- tries to reuse the repo's Sentinel orchestrator if available
- falls back to a local repo summarizer when external model connectivity is unavailable
- can inspect relevant files matching the user's prompt

## Files

- `agent.py`: CLI entrypoint
- `agents/workspace_agent.py`: core logic
- `agents/__init__.py`: package export
