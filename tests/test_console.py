"""Tests for the operator console API, using a fake surface plus one real-browser run."""

import json
from contextlib import asynccontextmanager

from fastapi.testclient import TestClient

from cua.console.app import create_app
from cua.console.runner import MemberLookupExecutor
from cua.surface import Click, Observation, TargetNotFound
from tests.conftest import DEMO_PASSWORD, DEMO_USERNAME

SECRET = "s3cret-pass"


class FakeSurface:
    """Pretends every action works and every page is the given URL and snapshot."""

    def __init__(self, url: str, snapshot: str = "", fail_on_click: str | None = None) -> None:
        self.url, self.snapshot, self.fail_on_click = url, snapshot, fail_on_click

    async def act(self, action) -> None:
        if isinstance(action, Click) and action.target.name == self.fail_on_click:
            raise TargetNotFound(f"no button named {self.fail_on_click!r}")

    async def perceive(self) -> Observation:
        return Observation(self.url, "Fake page", self.snapshot, b"\x89PNG fake")


def console(surface: FakeSurface) -> TestClient:
    @asynccontextmanager
    async def factory():
        yield surface

    executor = MemberLookupExecutor("http://target", "operator", SECRET, surface_factory=factory)
    return TestClient(create_app(executor))


def run_to_end(client: TestClient, member_id: str) -> tuple[dict, list[dict]]:
    response = client.post("/api/runs", json={"member_id": member_id})
    assert response.status_code == 201
    run = response.json()
    with client.stream("GET", f"/api/runs/{run['id']}/events") as stream:
        events = [json.loads(line[len("data: "):]) for line in stream.iter_lines() if line]
    return run, events


def test_lookup_streams_every_step_then_the_outcome():
    with console(FakeSurface("http://target/members/12345")) as client:
        run, events = run_to_end(client, "12345")
        types = [event["type"] for event in events]

        assert types == ["run.started"] + ["step.started", "step.completed"] * 6 + ["run.completed"]
        assert events[-1]["outcome"] == "member_found"
        assert client.get(f"/api/runs/{run['id']}").json()["status"] == "completed"
        assert client.get("/api/runs").json()[0]["id"] == run["id"]


def test_password_never_appears_in_events():
    with console(FakeSurface("http://target/members/12345")) as client:
        _, events = run_to_end(client, "12345")

        assert SECRET not in json.dumps(events)
        assert any("••••••" in event.get("text", "") for event in events)


def test_step_screenshots_are_served():
    with console(FakeSurface("http://target/members/12345")) as client:
        _, events = run_to_end(client, "12345")
        screenshot_url = next(e["screenshot"] for e in events if e["type"] == "step.completed")

        response = client.get(screenshot_url)
        assert response.headers["content-type"] == "image/png"
        assert response.content.startswith(b"\x89PNG")


def test_member_not_found_is_an_outcome_not_a_failure():
    surface = FakeSurface("http://target/members/search?member_id=99999",
                          "No member found with number 99999.")
    with console(surface) as client:
        _, events = run_to_end(client, "99999")

        assert events[-1] == {**events[-1], "type": "run.completed", "outcome": "member_not_found"}


def test_failed_step_ends_the_run_with_its_index():
    with console(FakeSurface("http://target/login", fail_on_click="Search")) as client:
        run, events = run_to_end(client, "12345")

        assert events[-1]["type"] == "run.failed"
        assert events[-1]["index"] == 5
        assert "Search" in events[-1]["error"]
        assert client.get(f"/api/runs/{run['id']}").json()["status"] == "failed"


def test_member_id_must_be_digits():
    with console(FakeSurface("http://target")) as client:
        assert client.post("/api/runs", json={"member_id": "12a45"}).status_code == 422


def test_runs_are_disabled_without_credentials():
    with TestClient(create_app(None)) as client:
        assert client.get("/api/status").json()["ready"] is False
        assert client.post("/api/runs", json={"member_id": "12345"}).status_code == 503


def test_frontend_is_served():
    with TestClient(create_app(None)) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Who are we looking up today?" in page.text
        assert client.get("/js/app.js").status_code == 200


def test_real_browser_lookup_against_mock_app(live_server_url):
    executor = MemberLookupExecutor(live_server_url, DEMO_USERNAME, DEMO_PASSWORD)
    with TestClient(create_app(executor)) as client:
        _, events = run_to_end(client, "31007")

        assert events[-1]["type"] == "run.completed"
        assert events[-1]["outcome"] == "member_found"
        assert 'cell "Samuel Okafor"' in events[-1]["snapshot"]
