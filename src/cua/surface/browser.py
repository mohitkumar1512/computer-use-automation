"""Playwright-backed web surface."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Page, async_playwright

from cua.surface.observation import Observation

VIEWPORT = {"width": 1280, "height": 800}


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

    def __init__(self, page: Page) -> None:
        self._page = page

    async def perceive(self) -> Observation:
        await self._page.wait_for_load_state()
        return Observation(
            url=self._page.url,
            title=await self._page.title(),
            aria_snapshot=await self._page.locator("body").aria_snapshot(),
            screenshot=await self._page.screenshot(full_page=True),
        )
