from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Optional

from ..rich_formatter import print_info


def _load_turns_from_path(path: Optional[str]) -> tuple[list[dict], Optional[Path]]:
    p: Optional[Path]
    if path:
        p = Path(path)
        if not p.exists():
            # Allow bare filename under default log dir
            p = Path("convo-logs") / path
            if not p.exists():
                return [], None
    else:
        log_dir = Path("convo-logs")
        if not log_dir.exists():
            return [], None
        files = sorted(log_dir.glob("chat_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        p = files[0] if files else None
        if not p:
            return [], None

    try:
        with open(p, "r", encoding="utf-8") as f:
            turns = json.load(f)
        # Filter to real turns
        filtered = [
            t for t in turns
            if isinstance(t, dict)
            and t.get("ai_response")
            and t.get("user_prompt")
            and t.get("user_prompt", "").lower() not in {"exit", "quit", "eof (ctrl+d)", "unexpected_exit"}
        ]
        return filtered, p
    except Exception:
        return [], p


def handle_resume_command(agent: Any, user_input: str) -> None:
    """Handle a /resume command in the REPL.

    Usage: /resume [filename-or-path]
    """
    try:
        parts = user_input.split(maxsplit=1)
        path = parts[1] if len(parts) > 1 else ""
        turns, p = _load_turns_from_path(path)
        if not p:
            print_info("No conversation logs found to resume.")
            return
        if hasattr(agent, 'preload_history_from_chatlog'):
            loaded = agent.preload_history_from_chatlog(turns)  # type: ignore[attr-defined]
            print_info(f"Loaded {loaded} prior turns from: {p}")
        else:
            print_info("This agent does not support resuming history in this mode.")
    except Exception as exc:
        print_info(f"Failed to resume: {exc}")


