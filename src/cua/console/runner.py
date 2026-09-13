"""Executes a member lookup for the console, reporting each step as it happens."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from cua.console.runs import Run
from cua.scripted import member_lookup_actions
from cua.surface import Observation, Surface, SurfaceError, WebSurface, describe, launch_page

SurfaceFactory = Callable[[], AbstractAsyncContextManager[Surface]]


@asynccontextmanager
async def browser_surface() -> AsyncIterator[Surface]:
    async with launch_page() as page:
        yield WebSurface(page)


def outcome_of(observation: Observation, member_id: str) -> str:
    """Classify where the lookup ended up. Proper checkpoints arrive with M12."""
    if observation.url.rstrip("/").endswith(f"/members/{member_id}"):
        return "member_found"
    if f"No member found with number {member_id}" in observation.aria_snapshot:
        return "member_not_found"
    return "unexpected_page"


class MemberLookupExecutor:
    """Runs the scripted (no LLM) member lookup against the target app."""

    def __init__(
        self,
        target_url: str,
        username: str,
        password: str,
        surface_factory: SurfaceFactory = browser_surface,
    ) -> None:
        self._target_url = target_url.rstrip("/")
        self._username = username
        self._password = password
        self._surface_factory = surface_factory

    async def __call__(self, run: Run) -> None:
        actions = member_lookup_actions(
            self._target_url, self._username, self._password, run.member_id
        )
        await run.emit({"type": "run.started", "member_id": run.member_id, "steps": len(actions)})
        async with self._surface_factory() as surface:
            result = await self._perform(run, surface, actions)
        # Announce the end only once the browser is closed, so a finished run holds no resources.
        await run.emit(result)

    async def _perform(self, run: Run, surface: Surface, actions: list) -> dict:
        """Emit step events as actions run; return the terminal event."""
        observation = None
        for index, action in enumerate(actions):
            await run.emit({"type": "step.started", "index": index, "text": describe(action)})
            try:
                await surface.act(action)
            except SurfaceError as error:
                return {"type": "run.failed", "index": index, "error": str(error)}
            observation = await surface.perceive()
            run.screenshots[index] = observation.screenshot
            await run.emit(
                {
                    "type": "step.completed",
                    "index": index,
                    "url": observation.url,
                    "title": observation.title,
                    "screenshot": f"/api/runs/{run.id}/steps/{index}/screenshot.png",
                }
            )
        return {
            "type": "run.completed",
            "outcome": outcome_of(observation, run.member_id),
            "url": observation.url,
            "snapshot": observation.aria_snapshot,
        }
