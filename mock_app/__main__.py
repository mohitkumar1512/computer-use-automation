"""Run the mock app:  python -m mock_app [--host 0.0.0.0] [--port 5000]"""

import argparse

from mock_app.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the mock credit-union app.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    create_app().run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
