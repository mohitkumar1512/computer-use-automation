"""Runs started from the console, and the event log each one streams to the browser.

Every run keeps its full event list, so a page that connects late (or reloads) replays the run
from the beginning and then follows it live.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

Event = dict[str, Any]
TERMINAL_EVENTS = {"run.completed", "run.failed"}


@dataclass
class Run:
    member_id: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "running"  # running | completed | failed
    events: list[Event] = field(default_factory=list)
    screenshots: dict[int, bytes] = field(default_factory=dict, repr=False)
    _changed: asyncio.Condition = field(default_factory=asyncio.Condition, repr=False)

    async def emit(self, event: Event) -> None:
        async with self._changed:
            self.events.append(event)
            if event["type"] == "run.completed":
                self.status = "completed"
            elif event["type"] == "run.failed":
                self.status = "failed"
            self._changed.notify_all()

    async def stream(self) -> AsyncIterator[Event]:
        """Yield every event so far, then new ones as they happen, ending at the terminal one."""
        sent = 0
        while True:
            async with self._changed:
                await self._changed.wait_for(lambda: len(self.events) > sent)
                pending = self.events[sent:]
            for event in pending:
                yield event
                sent += 1
                if event["type"] in TERMINAL_EVENTS:
                    return

    def summary(self) -> dict[str, str]:
        return {
            "id": self.id,
            "member_id": self.member_id,
            "status": self.status,
            "created_at": self.created_at,
        }


Executor = Callable[[Run], Awaitable[None]]


class RunManager:
    """Starts runs in the background and keeps them in memory for this server's lifetime."""

    def __init__(self, execute: Executor) -> None:
        self._execute = execute
        self._runs: dict[str, Run] = {}
        self._tasks: set[asyncio.Task] = set()  # hold references so tasks aren't collected

    def start(self, member_id: str) -> Run:
        run = Run(member_id=member_id)
        self._runs[run.id] = run
        task = asyncio.create_task(self._execute_safely(run))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return run

    def get(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def recent(self) -> list[Run]:
        return sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True)

    async def _execute_safely(self, run: Run) -> None:
        try:
            await self._execute(run)
        except Exception as error:  # a crashed run must still end, or its stream never closes
            await run.emit({"type": "run.failed", "error": f"Unexpected error: {error}"})
        if run.status == "running":
            await run.emit({"type": "run.failed", "error": "Run ended without a result."})
