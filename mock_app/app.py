"""Flask application factory for the mock credit-union app."""

import os
import secrets
from decimal import Decimal

from flask import Flask

from mock_app import auth, routes
from mock_app.store import Store


def format_money(value: str) -> str:
    return f"${Decimal(value):,.2f}"


def create_app() -> Flask:
    app = Flask(__name__)
    # A random key per process is fine for a mock: restarting simply logs everyone out.
    app.secret_key = os.environ.get("MOCK_APP_SECRET_KEY") or secrets.token_hex(32)
    app.extensions["store"] = Store()
    app.add_template_filter(format_money, "money")
    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    return app
