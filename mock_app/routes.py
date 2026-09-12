"""Member search and member detail pages."""

from flask import Blueprint, abort, redirect, render_template, request, url_for

from mock_app.auth import login_required
from mock_app.store import get_store

bp = Blueprint("members", __name__)


@bp.get("/")
def index():
    return redirect(url_for("members.search"))


@bp.get("/members/search")
@login_required
def search():
    member_id = request.args.get("member_id", "").strip()
    message = None
    if member_id:
        if get_store().find_member(member_id):
            return redirect(url_for("members.detail", member_id=member_id))
        message = f"No member found with number {member_id}."
    return render_template("search.html", member_id=member_id, message=message)


@bp.get("/members/<member_id>")
@login_required
def detail(member_id: str):
    member = get_store().find_member(member_id)
    if member is None:
        abort(404)
    return render_template("member.html", member=member)
