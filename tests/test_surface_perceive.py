"""Tests for WebSurface.perceive against the live mock app in a real (headless) browser."""

import asyncio

from cua.surface import Observation, WebSurface, launch_page
from tests.conftest import DEMO_PASSWORD, DEMO_USERNAME

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def perceive(base_url: str, path: str, *, log_in: bool = False) -> Observation:
    async def run() -> Observation:
        async with launch_page() as page:
            if log_in:  # test setup only — acting through the surface arrives in M3
                await page.goto(f"{base_url}/login")
                await page.fill("#username", DEMO_USERNAME)
                await page.fill("#password", DEMO_PASSWORD)
                await page.click("input[type=submit]")
                await page.wait_for_url("**/members/search")
            await page.goto(f"{base_url}{path}")
            return await WebSurface(page).perceive()

    return asyncio.run(run())


def test_login_page_exposes_labelled_controls(live_server_url):
    observation = perceive(live_server_url, "/login")

    assert observation.url == f"{live_server_url}/login"
    assert observation.title.startswith("Sign On")
    assert 'textbox "User ID:"' in observation.aria_snapshot
    assert 'textbox "Password:"' in observation.aria_snapshot
    assert 'button "Sign On"' in observation.aria_snapshot
    assert observation.screenshot.startswith(PNG_SIGNATURE)


def test_unauthenticated_visit_is_observed_after_redirect(live_server_url):
    observation = perceive(live_server_url, "/members/12345")

    assert observation.url.endswith("/login")


def test_member_detail_exposes_account_table(live_server_url):
    observation = perceive(live_server_url, "/members/12345", log_in=True)

    assert observation.title.startswith("Member 12345")
    assert 'cell "Jordan Rivera"' in observation.aria_snapshot
    assert 'cell "Share Savings"' in observation.aria_snapshot
    assert 'cell "$2,450.00"' in observation.aria_snapshot
    assert 'link "<< New Member Inquiry"' in observation.aria_snapshot


def test_observation_repr_omits_page_content(live_server_url):
    observation = perceive(live_server_url, "/members/12345", log_in=True)

    assert "900-12-3456" in observation.aria_snapshot  # fictional SSN is on the page...
    assert "900-12-3456" not in repr(observation)  # ...but never in the repr
    assert "screenshot" not in repr(observation)
