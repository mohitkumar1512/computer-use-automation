"""Operator login/logout, and the login_required guard for protected pages."""

from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from mock_app.store import get_store

bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "operator" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        operator = get_store().find_operator(request.form.get("username", ""))
        password = request.form.get("password", "")
        if operator and check_password_hash(operator["password_hash"], password):
            session.clear()
            session["operator"] = operator["display_name"]
            return redirect(url_for("members.search"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
