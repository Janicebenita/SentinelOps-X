import httpx
print(httpx.post("http://localhost:8000/api/demo/seed", timeout=10).json())
