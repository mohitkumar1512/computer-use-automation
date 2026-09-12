"""A hand-written member lookup with no LLM — proves the surface can act before a model drives it.

    CUA_USERNAME=... CUA_PASSWORD=... python -m cua.scripted 12345 [--base-url URL]

Credentials come from the environment so they never appear in code, arguments, or shell history.
"""

import argparse
import asyncio
import os
import sys
from collections.abc import Iterable

from cua.surface import Action, Click, Fill, Navigate, Observation, Surface, Target
from cua.surface import SurfaceError, WebSurface, launch_page


def member_lookup_actions(
    base_url: str, username: str, password: str, member_id: str
) -> list[Action]:
    """Sign on to the mock app and open a member's detail page."""
    return [
        Navigate(f"{base_url}/login"),
        Fill(Target("textbox", "User ID:"), username),
        Fill(Target("textbox", "Password:"), password),
        Click(Target("button", "Sign On")),
        Fill(Target("textbox", "Member Number:"), member_id),
        Click(Target("button", "Search")),
    ]


async def run_actions(surface: Surface, actions: Iterable[Action]) -> Observation:
    """Perform actions in order and return what the surface shows afterwards."""
    for action in actions:
        await surface.act(action)
    return await surface.perceive()


async def lookup(base_url: str, username: str, password: str, member_id: str) -> Observation:
    async with launch_page() as page:
        actions = member_lookup_actions(base_url, username, password, member_id)
        return await run_actions(WebSurface(page), actions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up a member in the mock app, no LLM.")
    parser.add_argument("member_id")
    parser.add_argument("--base-url", default="http://localhost:5000")
    args = parser.parse_args()

    username, password = os.environ.get("CUA_USERNAME"), os.environ.get("CUA_PASSWORD")
    if not username or not password:
        sys.exit("Set CUA_USERNAME and CUA_PASSWORD.")
    try:
        observation = asyncio.run(lookup(args.base_url, username, password, args.member_id))
    except SurfaceError as error:
        sys.exit(f"Lookup failed: {error}")
    print(f"# {observation.title}\n# {observation.url}\n{observation.aria_snapshot}")


if __name__ == "__main__":
    main()
