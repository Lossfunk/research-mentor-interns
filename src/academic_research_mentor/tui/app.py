from __future__ import annotations

from queue import Empty
from typing import Optional

from rich.markdown import Markdown
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, RichLog, Static

from ..runtime.events import EventSubscription, RuntimeEvent
from .session import TUISessionManager, ConversationOutcome


class MentorTUI(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        layout: horizontal;
        height: 1fr;
    }

    .column {
        layout: vertical;
        height: 1fr;
        padding: 0 1;
    }

    #conversation-pane {
        width: 2fr;
    }

    #side-pane {
        width: 1fr;
    }

    RichLog {
        border: round #444444;
        height: 1fr;
        padding: 0 1;
    }

    #status-log {
        height: auto;
        max-height: 8;
    }

    #input {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_conversation", "Clear conversation"),
        ("ctrl+r", "toggle_reasoning", "Toggle reasoning"),
    ]

    def __init__(
        self,
        *,
        session: Optional[TUISessionManager],
        subscription: Optional[EventSubscription],
        offline_reason: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._session = session
        self._subscription = subscription
        self._offline_reason = offline_reason
        self._reasoning_visible = reactive(True)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="body"):
            with Vertical(id="conversation-pane", classes="column"):
                yield Static("Conversation", id="conversation-title")
                yield RichLog(id="conversation-log", markup=True, highlight=False)
            with Vertical(id="side-pane", classes="column"):
                yield Static("Stage", id="stage-title")
                yield Static("", id="stage-display")
                yield Static("Reasoning", id="reasoning-title")
                yield RichLog(id="reasoning-log", markup=True, highlight=False)
                yield Static("Status", id="status-title")
                yield RichLog(id="status-log", markup=True, highlight=False)
        yield Input(placeholder="Ask the mentor...", id="input")
        yield Footer()

    def on_mount(self) -> None:
        input_widget = self.query_one(Input)
        if self._session is None:
            input_widget.placeholder = "Model unavailable — check API keys"
            input_widget.disabled = True
            if self._offline_reason:
                status_log = self.query_one("#status-log", RichLog)
                status_log.write(f"[bold red]Offline:[/bold red] {self._offline_reason}")
            return

        input_widget.focus()
        if self._subscription:
            self.set_interval(0.05, self._drain_events)

    def watch__reasoning_visible(self, visible: bool) -> None:
        reasoning_container: Widget = self.query_one("#reasoning-log")
        title_widget: Widget = self.query_one("#reasoning-title")
        reasoning_container.display = visible
        title_widget.display = visible

    def action_clear_conversation(self) -> None:
        self.query_one("#conversation-log", RichLog).clear()
        self.query_one("#reasoning-log", RichLog).clear()
        self.query_one("#status-log", RichLog).clear()
        stage_display = self.query_one("#stage-display", Static)
        stage_display.update("")

    def action_toggle_reasoning(self) -> None:
        self._reasoning_visible = not self._reasoning_visible

    @on(Input.Submitted)
    def handle_submit(self, event: Input.Submitted) -> None:
        if not self._session:
            return
        message = event.value.strip()
        event.input.value = ""
        if not message:
            return
        outcome = self._session.handle_user_message(message)
        if outcome.exit_command:
            event.input.disabled = True
            event.input.placeholder = "Session closed"
            self.exit()

    def _drain_events(self) -> None:
        if not self._subscription:
            return
        queue = self._subscription.queue
        try:
            while True:
                runtime_event = queue.get_nowait()
                self._handle_runtime_event(runtime_event)
        except Empty:
            return

    def _handle_runtime_event(self, runtime_event: RuntimeEvent) -> None:
        etype = runtime_event.type
        payload = runtime_event.payload

        if etype == "formatted_response":
            content = payload.get("content", "")
            title = payload.get("title") or "Mentor"
            conversation_log = self.query_one("#conversation-log", RichLog)
            conversation_log.write(Markdown(f"### {title}\n\n{content}"))
        elif etype == "user_input_display":
            content = payload.get("content", "")
            conversation_log = self.query_one("#conversation-log", RichLog)
            conversation_log.write(f"[bold cyan]You:[/bold cyan] {content}")
        elif etype == "agent_reasoning":
            content = payload.get("content", "")
            reasoning_log = self.query_one("#reasoning-log", RichLog)
            reasoning_log.write(Markdown(content))
        elif etype in {"print_info", "print_success"}:
            message = payload.get("message", "")
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[bold green]Info:[/bold green] {message}")
        elif etype == "print_error":
            message = payload.get("message", "")
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[bold red]Error:[/bold red] {message}")
        elif etype == "stage_badge":
            stage_code = payload.get("stage_code", "?")
            stage_name = payload.get("stage_name", "")
            confidence = payload.get("confidence", 0.0)
            stage_display = self.query_one("#stage-display", Static)
            stage_display.update(f"[b]{stage_code}[/b] — {stage_name} (conf {confidence:.2f})")
        elif etype == "tool_call_started":
            status_log = self.query_one("#status-log", RichLog)
            tool = payload.get("tool", "unknown")
            status_log.write(f"[yellow]Tool:[/] {tool} started")
        elif etype == "tool_call_finished":
            tool = payload.get("tool", "unknown")
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[green]Tool:[/] {tool} finished")
        elif etype == "tool_call_failed":
            status_log = self.query_one("#status-log", RichLog)
            tool = payload.get("tool", "unknown")
            error = payload.get("error", "")
            status_log.write(f"[red]Tool:[/] {tool} failed — {error}")
        elif etype == "tool_call_unavailable":
            status_log = self.query_one("#status-log", RichLog)
            tool = payload.get("tool", "unknown")
            status_log.write(f"[orange1]Tool:[/] {tool} unavailable")

    def on_unmount(self) -> None:
        if self._subscription:
            self._subscription.close()
        if self._session:
            self._session.close("tui_exit")
