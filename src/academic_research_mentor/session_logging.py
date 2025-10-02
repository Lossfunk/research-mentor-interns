from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class SessionLogManager:
    def __init__(self, log_dir: str = "convo-logs") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        base_session_id = f"chat_{ts}"
        session_dir = self._log_dir / base_session_id
        attempt = 1
        while session_dir.exists():
            attempt += 1
            session_dir = self._log_dir / f"{base_session_id}_{attempt}"
        self.session_id = session_dir.name
        self._session_dir = session_dir
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self.started_ms = int(time.time() * 1000)
        self._events_path = self._session_dir / f"{self.session_id}_events.jsonl"
        self._session_path = self._session_dir / f"{self.session_id}_session.json"
        self._events_file = self._events_path.open("a", encoding="utf-8")
        self._metadata: Dict[str, Any] = {
            "session_id": self.session_id,
            "started_ms": self.started_ms,
            "events_path": str(self._events_path),
            "session_dir": str(self._session_dir),
        }
        self._current_turn: Optional[int] = None
        self._turn_state: Dict[int, Dict[str, Any]] = {}
        self._closed = False
        self._log_event("session_started", {})

    def start_turn(self, turn: int, user_prompt: str) -> None:
        self._current_turn = turn
        self._turn_state[turn] = {"user_prompt": user_prompt}
        self._log_event("turn_started", {"user_prompt": user_prompt, "turn": turn}, turn=turn)

    def record_stage(self, stage: Dict[str, Any]) -> None:
        self._log_event("stage_detected", stage)

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._log_event(event_type, payload)

    def record_tool_calls(self, tool_calls: Any) -> None:
        self._log_event("tool_calls", {"tool_calls": tool_calls})

    def finalize_turn(self, turn: int, turn_payload: Dict[str, Any]) -> None:
        state = self._turn_state.get(turn, {})
        already_final = bool(state.get("_finalized"))
        merged = {**state, **turn_payload, "_finalized": True}
        self._turn_state[turn] = merged
        self._log_event("turn_updated" if already_final else "turn_finalized", turn_payload, turn=turn)
        if self._current_turn == turn:
            self._current_turn = None

    def link_transparency_run(self, run_id: str, tool_name: str) -> None:
        self._log_event("tool_run_linked", {"run_id": run_id, "tool": tool_name})

    def attach_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value
        self._flush_metadata()

    def finalize(self, exit_command: str) -> None:
        if self._closed:
            return
        self._metadata["ended_ms"] = int(time.time() * 1000)
        self._metadata["exit_command"] = exit_command
        self._flush_metadata()
        self._log_event("session_closed", {"exit_command": exit_command})
        try:
            self._events_file.flush()
            self._events_file.close()
        except Exception:
            pass
        self._closed = True

    def _flush_metadata(self) -> None:
        self._session_path.write_text(json.dumps(self._metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log_event(self, event_type: str, payload: Dict[str, Any], turn: Optional[int] = None) -> None:
        event = {
            "timestamp_ms": int(time.time() * 1000),
            "type": event_type,
            "turn": turn if turn is not None else self._current_turn,
            "payload": payload,
        }
        try:
            if not self._closed:
                self._events_file.write(json.dumps(event, ensure_ascii=False) + "\n")
                self._events_file.flush()
        except Exception:
            pass


_active_session_logger: Optional[SessionLogManager] = None


def set_active_session_logger(logger: Optional[SessionLogManager]) -> None:
    global _active_session_logger
    _active_session_logger = logger


def get_active_session_logger() -> Optional[SessionLogManager]:
    return _active_session_logger


def log_ui_event(event_type: str, payload: Dict[str, Any]) -> None:
    logger = get_active_session_logger()
    if logger:
        logger.log_event(event_type, payload)


def log_transparency_event(event: Dict[str, Any]) -> None:
    logger = get_active_session_logger()
    if logger:
        logger.log_event("tool_transparency", event)
