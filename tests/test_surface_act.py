"""Tests for WebSurface.act and the scripted member lookup, in a real (headless) browser."""

import asyncio

import pytest

from cua.scripted import member_lookup_actions, run_actions
from cua.surface import AmbiguousTarget, Click, Fill, Observation, Target, TargetNotFound
from cua.surface import WebSurface, launch_page
from tests.conftest import DEMO_PASSWORD, DEMO_USERNAME


def lookup(base_url: str, member_id: str) -> Observation:
    async def run() -> Observation:
        async with launch_page() as page:
            actions = member_lookup_actions(base_url, DEMO_USERNAME, DEMO_PASSWORD, member_id)
            return await run_actions(WebSurface(page), actions)

    return asyncio.run(run())


def act_on_html(html: str, action) -> None:
    """Perform one action on a static page, with a short timeout."""

    async def run() -> None:
        async with launch_page() as page:
            await page.set_content(html)
            await WebSurface(page, timeout_ms=300).act(action)

    asyncio.run(run())


def test_scripted_lookup_opens_member_detail(live_server_url):
    observation = lookup(live_server_url, "20488")

    assert observation.url == f"{live_server_url}/members/20488"
    assert 'cell "Priya Natarajan"' in observation.aria_snapshot
    assert 'cell "Auto Loan"' in observation.aria_snapshot


def test_scripted_lookup_of_unknown_member_stays_on_search(live_server_url):
    observation = lookup(live_server_url, "99999")

    assert "/members/search" in observation.url
    assert "No member found with number 99999." in observation.aria_snapshot


def test_click_on_missing_target_raises_target_not_found():
    with pytest.raises(TargetNotFound, match="Transfer Funds"):
        act_on_html("<button>Search</button>", Click(Target("button", "Transfer Funds")))


def test_names_match_exactly_not_by_substring():
    with pytest.raises(TargetNotFound):
        act_on_html("<button>Search Members</button>", Click(Target("button", "Search")))


def test_duplicate_names_raise_instead_of_guessing():
    html = "<button>Submit</button><button>Submit</button>"
    with pytest.raises(AmbiguousTarget, match="2 elements"):
        act_on_html(html, Click(Target("button", "Submit")))


def test_fill_repr_hides_typed_text():
    action = Fill(Target("textbox", "Password:"), "teller-demo-pass")

    assert "teller-demo-pass" not in repr(action)
