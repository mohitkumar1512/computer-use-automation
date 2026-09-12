"""In-memory data store for the mock app, seeded from the JSON files in data/."""

import copy
import json
from pathlib import Path
from typing import TypedDict

from flask import current_app

DATA_DIR = Path(__file__).parent / "data"


class Account(TypedDict):
    account_number: str
    type: str
    status: str
    balance: str  # exact decimal as text — money is never a float


class Member(TypedDict):
    member_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    ssn: str
    phone: str
    email: str
    member_since: str
    accounts: list[Account]


class Operator(TypedDict):
    username: str
    display_name: str
    role: str
    password_hash: str


def _load_json(filename: str) -> dict:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


class Store:
    """Holds operators and members in memory. reset() restores the seed state."""

    def __init__(self) -> None:
        self._seed_members: list[Member] = _load_json("members.json")["members"]
        self._seed_operators: list[Operator] = _load_json("operators.json")["operators"]
        self.reset()

    def reset(self) -> None:
        self.members = {m["member_id"]: copy.deepcopy(m) for m in self._seed_members}
        self.operators = {o["username"]: copy.deepcopy(o) for o in self._seed_operators}

    def find_member(self, member_id: str) -> Member | None:
        return self.members.get(member_id.strip())

    def find_operator(self, username: str) -> Operator | None:
        return self.operators.get(username.strip())


def get_store() -> Store:
    """The Store attached to the running Flask app."""
    return current_app.extensions["store"]
