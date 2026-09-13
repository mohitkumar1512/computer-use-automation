"""The operator console: a small API for starting and following runs, plus the static frontend."""

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cua.console.runs import Executor, Run, RunManager

STATIC_DIR = Path(__file__).parent / "static"


class StartRun(BaseModel):
    member_id: str = Field(pattern=r"^\d{1,10}$")


def create_app(execute: Executor | None) -> FastAPI:
    """execute is None when the console isn't configured to reach a target app."""
    app = FastAPI(title="cua console", docs_url=None, redoc_url=None)
    manager = RunManager(execute) if execute else None

    def find_run(run_id: str) -> Run:
        run = manager.get(run_id) if manager else None
        if run is None:
            raise HTTPException(404, "Run not found.")
        return run

    @app.get("/api/status")
    async def status() -> dict:
        return {"ready": manager is not None, "capability": "member_lookup", "llm": False}

    @app.post("/api/runs", status_code=201)
    async def start_run(body: StartRun) -> dict:
        if manager is None:
            raise HTTPException(503, "Set CUA_USERNAME and CUA_PASSWORD to enable runs.")
        return manager.start(body.member_id).summary()

    @app.get("/api/runs")
    async def list_runs() -> list[dict]:
        return [run.summary() for run in manager.recent()] if manager else []

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str) -> dict:
        return find_run(run_id).summary()

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str) -> StreamingResponse:
        run = find_run(run_id)

        async def server_sent_events() -> AsyncIterator[str]:
            async for event in run.stream():
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(server_sent_events(), media_type="text/event-stream")

    @app.get("/api/runs/{run_id}/steps/{index}/screenshot.png")
    async def step_screenshot(run_id: str, index: int) -> Response:
        screenshot = find_run(run_id).screenshots.get(index)
        if screenshot is None:
            raise HTTPException(404, "Screenshot not found.")
        return Response(screenshot, media_type="image/png", headers={"Cache-Control": "no-store"})

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app
