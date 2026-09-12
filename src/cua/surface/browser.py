"""Playwright-backed web surface."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Locator, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from cua.surface.actions import Action, Click, Fill, Navigate, Target
from cua.surface.errors import AmbiguousTarget, TargetNotFound
from cua.surface.observation import Observation

VIEWPORT = {"width": 1280, "height": 800}
DEFAULT_TIMEOUT_MS = 5_000


def chromium_executable() -> str | None:
    """Replit provides a matching Chromium; elsewhere, Playwright uses its own download."""
    return os.environ.get("REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE") or None


@asynccontextmanager
async def launch_page(*, headless: bool = True) -> AsyncIterator[Page]:
    """Start Chromium and yield a fresh page; the browser is closed on exit."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=chromium_executable(), headless=headless
        )
        try:
            yield await browser.new_page(viewport=VIEWPORT)
        finally:
            await browser.close()


class WebSurface:
    """A Surface over a single Playwright page."""

    def __init__(self, page: Page, *, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> None:
        self._page = page
        self._timeout_ms = timeout_ms

    async def perceive(self) -> Observation:
        await self._page.wait_for_load_state()
        return Observation(
            url=self._page.url,
            title=await self._page.title(),
            aria_snapshot=await self._page.locator("body").aria_snapshot(),
            screenshot=await self._page.screenshot(full_page=True),
        )

    async def act(self, action: Action) -> None:
        match action:
            case Navigate(url=url):
                await self._page.goto(url)
            case Click(target=target):
                await (await self._locate(target)).click(timeout=self._timeout_ms)
            case Fill(target=target, text=text):
                await (await self._locate(target)).fill(text, timeout=self._timeout_ms)
            case _:
                raise TypeError(f"Unsupported action: {action!r}")

    async def _locate(self, target: Target) -> Locator:
        """Wait for an element matching target, and refuse to guess between several."""
        locator = self._page.get_by_role(target.role, name=target.name, exact=True)
        try:
            await locator.first.wait_for(state="visible", timeout=self._timeout_ms)
        except PlaywrightTimeoutError:
            raise TargetNotFound(f"no {target.role} named {target.name!r}") from None
        count = await locator.count()
        if count > 1:
            raise AmbiguousTarget(f"{count} elements match {target.role} {target.name!r}")
        return locator
