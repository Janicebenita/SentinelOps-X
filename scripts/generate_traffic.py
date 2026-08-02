import httpx
payload = {"items": [{"product_id": 1, "quantity": 2}], "discount_code": "SAVE10", "region": "TN"}
for _ in range(8):
    print(httpx.post("http://localhost:8001/checkout", json=payload, timeout=5).status_code)
