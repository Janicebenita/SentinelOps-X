from __future__ import annotations

import logging
import time
import traceback
import uuid
from decimal import Decimal
from typing import TypedDict, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from .observability import COUNTERS, LATENCIES, Span, append_jsonl, event, prometheus_text, request_id_var, trace_id_var

logger = logging.getLogger("demo_app")
logging.basicConfig(level=logging.INFO, format="%(message)s")
app = FastAPI(title="Sentinel Shop", version="0.1.0")
class Product(TypedDict):
    id: int
    name: str
    price: Decimal
PRODUCTS: dict[int, Product] = {1: {"id": 1, "name": "Telemetry Mug", "price": Decimal("24.00")}, 2: {"id": 2, "name": "On-call Hoodie", "price": Decimal("64.00")}}
TAX_RATES: dict[str, Decimal | None] = {"CA": Decimal("0.0725"), "NY": Decimal("0.04"), "TN": None}

class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=20)
class CheckoutRequest(BaseModel):
    items: list[CartItem]
    discount_code: str | None = None
    region: str

@app.middleware("http")
async def observe(request: Request, call_next):
    rid, trace = request.headers.get("x-request-id", str(uuid.uuid4())), str(uuid.uuid4())
    request_id_var.set(rid); trace_id_var.set(trace)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        event(logger, logging.ERROR, "request_failed", path=request.url.path, error=str(exc), stack_trace=traceback.format_exc())
        response = JSONResponse(status_code=500, content={"detail": "internal checkout error", "request_id": rid})
    latency = round((time.perf_counter()-started)*1000, 3)
    COUNTERS[(request.method, request.url.path, response.status_code)] += 1
    metric = {"timestamp": time.time(), "method": request.method, "path": request.url.path, "status": response.status_code, "latency_ms": latency}
    LATENCIES.append(metric); append_jsonl("data/metrics/demo.jsonl", metric)
    response.headers["x-request-id"] = rid
    return response

@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}
@app.get("/products")
def products() -> list[dict[str, object]]: return [{**p, "price": str(p["price"])} for p in PRODUCTS.values()]
@app.post("/cart")
def cart(items: list[CartItem]) -> dict[str, object]:
    subtotal = sum(PRODUCTS[i.product_id]["price"] * i.quantity for i in items)
    return {"items": [i.model_dump() for i in items], "subtotal": str(subtotal)}
@app.post("/checkout")
def checkout(order: CheckoutRequest) -> dict[str, str]:
    with Span("checkout.calculate", region=order.region, discount=order.discount_code):
        subtotal = sum(PRODUCTS[i.product_id]["price"] * i.quantity for i in order.items)
        discount = subtotal * Decimal("0.10") if order.discount_code == "SAVE10" else Decimal("0")
        taxable = subtotal - discount
        rate = cast(Decimal | None, TAX_RATES.get(order.region, Decimal("0")))
        # SEEDED BUG: TN's legacy rate is null and only reaches this operation on discounted orders.
        tax = taxable * cast(Decimal, rate) if order.discount_code else taxable * (rate or Decimal("0"))
        total = taxable + tax
        event(logger, logging.INFO, "checkout_completed", region=order.region, total=str(total))
        return {"subtotal": str(subtotal), "discount": str(discount), "tax": str(tax), "total": str(total)}
@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str: return prometheus_text()
