from __future__ import annotations

import json
from pathlib import Path

from academic_research_mentor.chat_logger import ChatLogger
from academic_research_mentor.session_logging import SessionLogManager
from academic_research_mentor.cli.resume import _load_turns_from_path


def _write_sample_turn(logger: ChatLogger) -> None:
    logger.add_turn(
        user_prompt="Hello",
        tool_calls=[],
        ai_response="Hi there!",
        stage={"stage": "A"},
    )


def test_logs_are_written_inside_session_directory(tmp_path) -> None:
    manager = SessionLogManager(log_dir=str(tmp_path))
    try:
        chat_logger = ChatLogger(log_dir=str(tmp_path), session_logger=manager)
        _write_sample_turn(chat_logger)
        saved_path = Path(chat_logger.save_session())

        session_dir = tmp_path / manager.session_id
        assert session_dir.is_dir()
        assert saved_path.parent == session_dir
        assert saved_path.name == f"{manager.session_id}.json"
        assert (session_dir / f"{manager.session_id}_events.jsonl").exists()

        manager.finalize("exit")
        session_meta = session_dir / f"{manager.session_id}_session.json"
        assert session_meta.exists()

        metadata = json.loads(session_meta.read_text(encoding="utf-8"))
        assert metadata.get("session_dir") == str(session_dir)
        assert metadata.get("chat_log_path") == str(saved_path)
    finally:
        manager.finalize("test_clean")


def test_resume_loader_handles_session_directory(tmp_path, monkeypatch) -> None:
    log_root = tmp_path / "convo-logs"
    manager = SessionLogManager(log_dir=str(log_root))
    try:
        chat_logger = ChatLogger(log_dir=str(log_root), session_logger=manager)
        _write_sample_turn(chat_logger)
        log_path = Path(chat_logger.save_session())
        manager.finalize("exit")

        # Switch working directory so resume helper finds default convo-logs
        monkeypatch.chdir(tmp_path)

        turns, resolved = _load_turns_from_path(str(log_path.parent))
        assert resolved == log_path
        assert len(turns) == 1
        assert turns[0]["ai_response"] == "Hi there!"

        turns_auto, resolved_auto = _load_turns_from_path(None)
        assert resolved_auto == log_path
        assert len(turns_auto) == 1
    finally:
        manager.finalize("test_clean")
