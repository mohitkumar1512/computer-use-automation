"""Tests for the mock app's seeded in-memory store."""

from decimal import Decimal

from mock_app.store import Store


def test_seed_data_loads_members_and_operators():
    store = Store()
    assert set(store.members) == {"12345", "20488", "31007"}
    assert "teller1" in store.operators


def test_find_member_ignores_surrounding_whitespace():
    assert Store().find_member("  12345 ")["last_name"] == "Rivera"


def test_find_member_returns_none_for_unknown_id():
    assert Store().find_member("99999") is None


def test_reset_discards_changes():
    store = Store()
    store.members["12345"]["accounts"][0]["balance"] = "0.00"
    store.reset()
    assert store.members["12345"]["accounts"][0]["balance"] == "2450.00"


def test_balances_are_exact_two_place_decimals():
    for member in Store().members.values():
        for account in member["accounts"]:
            assert isinstance(account["balance"], str)
            assert Decimal(account["balance"]).as_tuple().exponent == -2


def test_seed_pii_is_obviously_fictional():
    for member in Store().members.values():
        assert member["ssn"].startswith("9")
        assert member["phone"].startswith("555-01")
        assert member["email"].endswith("@example.com")


def test_operators_store_only_password_hashes():
    for operator in Store().operators.values():
        assert "password" not in operator
        assert operator["password_hash"].startswith("scrypt:")
