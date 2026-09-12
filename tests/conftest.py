"""Shared pytest fixtures."""

import pytest

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
