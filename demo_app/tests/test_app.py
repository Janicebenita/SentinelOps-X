from fastapi.testclient import TestClient
from demo_app.app.main import TAX_RATES, app

client = TestClient(app)
def test_health_and_products():
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/products").json()) == 2
def test_cart():
    assert client.post("/cart", json=[{"product_id": 1, "quantity": 2}]).json()["subtotal"] == "48.00"
def test_checkout_without_discount():
    assert client.post("/checkout", json={"items": [{"product_id": 1, "quantity": 2}], "region": "TN"}).status_code == 200
def test_checkout_with_discount_other_region():
    assert client.post("/checkout", json={"items": [{"product_id": 1, "quantity": 2}], "discount_code": "SAVE10", "region": "CA"}).status_code == 200
def test_seeded_discount_tn_fixture():
    assert TAX_RATES["TN"] is None
