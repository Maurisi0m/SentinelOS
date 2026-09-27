#!/usr/bin/env python3
"""Simple CLI entrypoint for the local workspace agent."""

from __future__ import annotations

import argparse
import sys

from agents.workspace_agent import WorkspaceAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a lightweight workspace-aware coding agent for this repository."
    )
    parser.add_argument(
        "--prompt",
        "-p",
        default="Summarize this repository and point me to the best entry points.",
        help="The task or question to answer.",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default=".",
        help="Path to the workspace root to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Start an interactive prompt loop instead of running a single command.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    agent = WorkspaceAgent(args.workspace)

    if args.interactive:
        print("Workspace agent ready. Type 'exit' to quit.")
        while True:
            try:
                prompt = input("agent> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not prompt or prompt.lower() in {"exit", "quit", "q"}:
                break
            print(agent.run_prompt(prompt))
        return 0

    print(agent.run_prompt(args.prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
