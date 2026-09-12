"""Tests for the mock app's login, search, and member detail pages."""

from tests.conftest import DEMO_PASSWORD, DEMO_USERNAME


def test_protected_pages_redirect_to_login(client):
    response = client.get("/members/search")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_with_wrong_password_shows_error(client):
    response = client.post("/login", data={"username": DEMO_USERNAME, "password": "wrong"})
    assert b"Invalid username or password." in response.data


def test_login_with_valid_credentials_goes_to_search(client):
    response = client.post("/login", data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/members/search")


def test_search_for_existing_member_redirects_to_detail(logged_in_client):
    response = logged_in_client.get("/members/search?member_id=12345")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/members/12345")


def test_search_for_unknown_member_shows_message(logged_in_client):
    response = logged_in_client.get("/members/search?member_id=99999")
    assert b"No member found with number 99999." in response.data


def test_member_detail_shows_accounts_and_formatted_balances(logged_in_client):
    page = logged_in_client.get("/members/12345").data
    assert b"Jordan Rivera" in page
    assert b"Share Savings" in page
    assert b"$2,450.00" in page


def test_logout_ends_the_session(logged_in_client):
    logged_in_client.post("/logout")
    response = logged_in_client.get("/members/search")
    assert response.headers["Location"].endswith("/login")
