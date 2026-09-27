from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, List


class WorkspaceAgent:
    """A lightweight repository-aware agent for local coding tasks.

    It provides a predictable fallback when external LLM tooling is unavailable,
    while still attempting to use the repo's existing Sentinel orchestration if it
    can be imported cleanly.
    """

    def __init__(self, workspace_root: str | os.PathLike[str] | None = None) -> None:
        self.workspace_root = Path(workspace_root or ".").resolve()
        self.sentinel_agent = self._load_sentinel_agent()

    def _load_sentinel_agent(self):
        try:
            sentinel_dir = self.workspace_root / "export" / "ubuntu_server"
            if not sentinel_dir.exists():
                return None
            sys.path.insert(0, str(sentinel_dir))
            from sentinel_orchestrator import SentinelAgent  # type: ignore

            return SentinelAgent()
        except Exception:
            return None

    def run_prompt(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            return "No prompt provided."

        if self.sentinel_agent is not None:
            try:
                answer, _, _ = self.sentinel_agent.chat_step(prompt)
                if answer and not answer.startswith("[ERROR"):
                    return answer
            except Exception:
                pass

        lower = prompt.lower()
        if any(token in lower for token in ["summary", "overview", "repo", "what is this", "describe"]):
            return self.summarize_repository()

        files = self.find_relevant_files(prompt)
        if files:
            return self.inspect_files(files, prompt)

        return self.summarize_repository() + "\n\nNo specific file match was identified from the prompt, so I returned the repo overview."

    def summarize_repository(self) -> str:
        root = self.workspace_root
        entries = sorted(p.name for p in root.iterdir())
        python_files = sorted(
            str(path.relative_to(root))
            for path in root.rglob("*.py")
            if ".venv" not in path.parts and "site-packages" not in path.parts
        )[:12]

        summary = [
            "Sentinel workspace overview:",
            f"- Root: {root}",
            f"- Top-level entries: {', '.join(entries[:20]) if entries else 'none'}",
            f"- Python entrypoints: {', '.join(python_files) if python_files else 'none'}",
            "",
            "This project appears to be a research + tooling workspace focused on a local AI agent, benchmarking, datasets, and model export workflows.",
            "",
            "Likely starting points:",
            "- agent.py: CLI entrypoint for the local workspace agent.",
            "- export/ubuntu_server/sentinel_orchestrator.py: the main orchestrator / tool-calling agent implementation.",
            "- test_agentic_tools.py: validation for file, shell, and file-system tool behavior.",
            "- dataset/: data-generation and dataset-compilation scripts.",
            "- benchmark/: benchmarking, reporting, and simulation assets.",
            "- training/: adapter training and model fine-tuning pipeline components.",
        ]
        return "\n".join(summary)

    def find_relevant_files(self, prompt: str) -> List[str]:
        keywords = [token for token in re.findall(r"[A-Za-z0-9_\-]+", prompt.lower()) if len(token) > 2]
        if not keywords:
            return []

        matches: List[str] = []
        for candidate in self.workspace_root.rglob("*"):
            if candidate.is_dir():
                continue
            name = candidate.name.lower()
            if any(keyword in name for keyword in keywords):
                matches.append(str(candidate.relative_to(self.workspace_root)))

        # Exclude common noisy matches such as .pyc or venv files.
        filtered = [item for item in matches if not item.startswith(".venv") and "site-packages" not in item]
        return filtered[:10]

    def inspect_files(self, files: Iterable[str], prompt: str) -> str:
        lines: List[str] = [f"Relevant files for prompt: {prompt}"]
        for relative in list(files)[:5]:
            full = self.workspace_root / relative
            if not full.exists():
                continue
            try:
                with full.open("r", encoding="utf-8", errors="replace") as handle:
                    content = handle.read().splitlines()
            except Exception:
                continue

            preview = content[:40]
            lines.append(f"\n--- {relative} ---")
            if preview:
                lines.append("\n".join(f"{idx + 1}: {line}" for idx, line in enumerate(preview)))
            else:
                lines.append("(empty file)")

        return "\n".join(lines)


if __name__ == "__main__":
    agent = WorkspaceAgent()
    print(agent.run_prompt("Summarize this repository."))
