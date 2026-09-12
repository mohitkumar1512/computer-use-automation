"""Shared pytest fixtures."""

import threading

import pytest
from werkzeug.serving import make_server

from mock_app.app import create_app

DEMO_USERNAME = "teller1"
DEMO_PASSWORD = "teller-demo-pass"


@pytest.fixture
def mock_app():
    return create_app()


@pytest.fixture
def client(mock_app):
    return mock_app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post("/login", data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    return client


@pytest.fixture(scope="session")
def live_server_url():
    """The mock app served over real HTTP on a free port, for browser tests."""
    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()
