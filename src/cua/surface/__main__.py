"""Perceive a page from the command line:  python -m cua.surface URL [--out DIR]"""

import argparse
import asyncio
from pathlib import Path

from cua.surface.browser import WebSurface, launch_page
from cua.surface.observation import Observation


async def observe(url: str) -> Observation:
    async with launch_page() as page:
        await page.goto(url)
        return await WebSurface(page).perceive()


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a page's accessibility snapshot.")
    parser.add_argument("url")
    parser.add_argument("--out", type=Path, help="also write snapshot.yaml and screenshot.png here")
    args = parser.parse_args()

    observation = asyncio.run(observe(args.url))
    print(f"# {observation.title}\n# {observation.url}\n{observation.aria_snapshot}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "snapshot.yaml").write_text(observation.aria_snapshot + "\n", encoding="utf-8")
        (args.out / "screenshot.png").write_bytes(observation.screenshot)
        print(f"# wrote {args.out}/snapshot.yaml and screenshot.png")


if __name__ == "__main__":
    main()
