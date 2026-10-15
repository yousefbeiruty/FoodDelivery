import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    http, _ = client
    response = await http.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "FreshBite"}


@pytest.mark.asyncio
async def test_register_login_and_profile_update(client):
    http, _ = client
    registration = await http.post(
        "/api/auth/register",
        json={"email": "customer@example.com", "password": "freshbite123", "full_name": "Test Customer"},
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "customer@example.com"
    assert "hashed_password" not in registration.json()

    login = await http.post(
        "/api/auth/token",
        data={"username": "customer@example.com", "password": "freshbite123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    profile = await http.get("/api/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "Test Customer"

    updated = await http.patch(
        "/api/users/me", headers=headers, json={"full_name": "Updated Customer", "phone_number": "+962790000000"}
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Customer"
    assert updated.json()["phone_number"] == "+962790000000"


@pytest.mark.asyncio
async def test_restaurant_search_category_and_menu(client):
    http, ids = client
    restaurants = await http.get("/api/restaurants/", params={"search": "test kitchen", "category": "burgers"})
    assert restaurants.status_code == 200
    assert len(restaurants.json()) == 1
    assert restaurants.json()[0]["id"] == ids["restaurant_id"]

    menu = await http.get(f"/api/restaurants/{ids['restaurant_id']}")
    assert menu.status_code == 200
    assert menu.json()["menu_items"][0]["name"] == "Garden Burger"
    assert menu.json()["menu_items"][0]["image_url"] == "/static/menu/burgers.svg"


@pytest.mark.asyncio
async def test_quote_place_order_history_and_status_update(client):
    http, ids = client
    await http.post(
        "/api/auth/register",
        json={"email": "orders@example.com", "password": "freshbite123", "full_name": "Order Customer"},
    )
    login = await http.post(
        "/api/auth/token", data={"username": "orders@example.com", "password": "freshbite123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    lines = [{"menu_item_id": ids["menu_item_id"], "quantity": 2}]

    quote = await http.post("/api/orders/quote", headers=headers, json={"items": lines, "promo_code": "FRESH10", "driver_tip": 1})
    assert quote.status_code == 200
    assert quote.json() == {
        "subtotal": 12.0,
        "delivery_fee": 2.5,
        "driver_tip": 1.0,
        "discount": 1.2,
        "total_amount": 14.3,
    }

    placed = await http.post(
        "/api/orders/",
        headers=headers,
        json={"items": lines, "promo_code": "FRESH10", "driver_tip": 1, "delivery_address": "12 Garden Street, Amman"},
    )
    assert placed.status_code == 201
    order = placed.json()
    assert order["total_amount"] == 14.3
    assert order["delivery_status"] == "Placed"
    order_id = order["id"]

    history = await http.get("/api/orders/", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    status = await http.patch(
        f"/api/orders/{order_id}/status",
        headers=headers,
        json={
            "delivery_status": "On the Way",
            "driver_name": "Sam",
            "estimated_time": "12 min",
            "driver_latitude": 31.95,
            "driver_longitude": 35.91,
        },
    )
    assert status.status_code == 200
    assert status.json()["delivery_status"] == "On the Way"
    assert status.json()["driver_name"] == "Sam"

    details = await http.get(f"/api/orders/{order_id}", headers=headers)
    assert details.status_code == 200
    assert details.json()["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_order_endpoints_require_authentication(client):
    http, _ = client
    quote = await http.post("/api/orders/quote", json={"items": [{"menu_item_id": 1, "quantity": 1}]})
    history = await http.get("/api/orders/")
    assert quote.status_code == 401
    assert history.status_code == 401
