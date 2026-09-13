"""Run the operator console:  python -m cua.console [--port 8000] [--target-url URL]

Credentials for the target app come from CUA_USERNAME / CUA_PASSWORD. Without them the console
still starts, but explains that runs are disabled.
"""

import argparse
import os

import uvicorn

from cua.console.app import create_app
from cua.console.runner import MemberLookupExecutor


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the cua operator console.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--target-url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    username, password = os.environ.get("CUA_USERNAME"), os.environ.get("CUA_PASSWORD")
    executor = (
        MemberLookupExecutor(args.target_url, username, password)
        if username and password
        else None
    )
    uvicorn.run(create_app(executor), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
