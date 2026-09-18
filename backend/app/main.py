from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import auth
from app import cash as cash_svc
from app import orders as order_svc
from app.deployment import deployment_for
from app.mechanisms import mechanism_for
from app.migrate import apply as apply_migrations
from app.profiles import PROFILES, resolve_modules
from app.seed import ensure_demo_venue
from app.serializers import product_out, space_out, station_out
from app.settings import settings


class OpenOrderIn(BaseModel):
    space_id: int
    cover_count: int | None = None
    dining_option: str | None = None


class AddItemIn(BaseModel):
    product_id: int
    qty: int = Field(default=1, ge=1)
    notes: str | None = None
    modifier_ids: list[int] = []


class BumpIn(BaseModel):
    action: str


class OpenShiftIn(BaseModel):
    opening_cash_cents: int = 0


class CloseShiftIn(BaseModel):
    counted_cash_cents: int


class PayIn(BaseModel):
    method: str
    amount_cents: int
    tip_cents: int = 0


class LoginIn(BaseModel):
    pin: str


class MoveItemIn(BaseModel):
    to_space_id: int


class MergeOrderIn(BaseModel):
    onto_order_id: int


class DiscountIn(BaseModel):
    type: str | None = None
    value: int = 0


class TaxIn(BaseModel):
    enabled: bool = False
    bps: int = 1500


CURRENCY_SYMBOL = {"NIO": "C$", "USD": "$"}


def current_profile() -> str:
    profile = settings.hermes_profile.strip().lower()
    return profile if profile in PROFILES else "restaurant"


def currency_pair() -> tuple[str, str]:
    code = (settings.hermes_currency or "NIO").strip().upper()
    if code not in CURRENCY_SYMBOL:
        code = "NIO"
    return code, CURRENCY_SYMBOL[code]


def instance_payload(seed: dict | None = None) -> dict:
    profile = current_profile()
    modules = resolve_modules(profile, settings.hermes_modules)
    mech = mechanism_for(profile)
    currency, symbol = currency_pair()
    payload = {
        "name": settings.app_name,
        "env": settings.app_env,
        "profile": profile,
        "profile_label": PROFILES[profile]["label"],
        "modules": modules,
        "mechanism": mech,
        "deployment": deployment_for(settings.hermes_deployment),
        "tagline": "El mensaje llega.",
        "database": bool(settings.database_url),
        "currency": currency,
        "symbol": symbol,
    }
    if seed and seed.get("venue"):
        payload["venue"] = {
            "id": seed["venue"]["id"],
            "name": seed["venue"]["name"],
            "slug": seed["venue"]["slug"],
            "tax_enabled": bool(seed["venue"].get("tax_enabled")),
            "tax_bps": int(seed["venue"].get("tax_bps") or 0),
            "currency": currency,
            "symbol": symbol,
        }
        payload["counts"] = {
            "spaces": len(seed.get("spaces") or []),
            "stations": len(seed.get("stations") or []),
            "products": len(seed.get("products") or []),
        }
    return payload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        apply_migrations()
        ensure_demo_venue()
        auth.ensure_users()
    except Exception as exc:  # noqa: BLE001
        print(f"hermes: seed skipped ({exc})")
    yield


app = FastAPI(title="Hermes OS", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_role(request: Request, call_next):
    cap = auth.cap_for_path(request.method, request.url.path)
    if cap:
        token = request.headers.get("authorization") or request.headers.get("x-hermes-token")
        user = auth.resolve(token)
        if not auth.allow(user, cap):
            return JSONResponse({"detail": "No autorizado"}, status_code=401)
    return await call_next(request)


def _need_seed() -> dict:
    try:
        apply_migrations()
        seed = ensure_demo_venue()
        auth.ensure_users()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {exc}") from exc
    if not seed:
        raise HTTPException(status_code=503, detail="DATABASE_URL no configurada")
    return seed


def _ok(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"ok": True, "name": settings.app_name}


@app.post("/api/login")
def login(body: LoginIn):
    _need_seed()
    return _ok(auth.login, body.pin)


@app.post("/api/logout")
def logout(request: Request):
    auth.logout(request.headers.get("authorization") or request.headers.get("x-hermes-token"))
    return {"ok": True}


@app.get("/api/cds")
def cds():
    _need_seed()
    return _ok(order_svc.cds_ticket)


@app.get("/api/instance")
def instance():
    try:
        seed = ensure_demo_venue()
    except Exception:
        seed = None
    return instance_payload(seed)


@app.get("/api/spaces")
def list_spaces():
    return [space_out(s) for s in _need_seed()["spaces"]]


@app.get("/api/stations")
def list_stations():
    return [station_out(s) for s in _need_seed()["stations"]]


@app.get("/api/products")
def list_products():
    return [product_out(p) for p in _need_seed()["products"]]


@app.get("/api/orders")
def list_orders():
    _need_seed()
    return _ok(order_svc.list_open)


@app.post("/api/orders")
def create_order(body: OpenOrderIn):
    _need_seed()
    return _ok(order_svc.open_order, body.space_id, body.cover_count, body.dining_option)


@app.post("/api/orders/{order_id}/items")
def add_item(order_id: int, body: AddItemIn):
    _need_seed()
    return _ok(
        order_svc.add_item,
        order_id,
        body.product_id,
        body.qty,
        body.notes,
        body.modifier_ids,
    )


@app.post("/api/orders/{order_id}/send")
def send_order(order_id: int):
    _need_seed()
    return _ok(order_svc.send_order, order_id)


@app.post("/api/orders/{order_id}/deliver")
def deliver_order(order_id: int):
    _need_seed()
    return _ok(order_svc.deliver_order, order_id)


@app.post("/api/orders/{order_id}/close")
def close_order(order_id: int):
    _need_seed()
    return _ok(order_svc.close_order, order_id)


@app.post("/api/items/{item_id}/bump")
def bump_item(item_id: int, body: BumpIn):
    _need_seed()
    return _ok(order_svc.bump_item, item_id, body.action)


@app.post("/api/items/{item_id}/void")
def void_item(item_id: int):
    _need_seed()
    return _ok(order_svc.void_item, item_id)


@app.post("/api/items/{item_id}/move")
def move_item(item_id: int, body: MoveItemIn):
    _need_seed()
    return _ok(order_svc.move_item, item_id, body.to_space_id)


@app.post("/api/orders/{order_id}/merge")
def merge_order(order_id: int, body: MergeOrderIn):
    _need_seed()
    return _ok(order_svc.merge_order, order_id, body.onto_order_id)


@app.post("/api/orders/{order_id}/discount")
def set_discount(order_id: int, body: DiscountIn):
    _need_seed()
    return _ok(order_svc.set_discount, order_id, body.type, body.value)


@app.post("/api/venue/tax")
def set_venue_tax(body: TaxIn):
    _need_seed()
    return _ok(order_svc.set_venue_tax, body.enabled, body.bps)


@app.get("/api/stations/{station_key}/tickets")
def station_tickets(station_key: str):
    _need_seed()
    return _ok(order_svc.station_tickets, station_key)


@app.get("/api/kds")
def kds_board():
    _need_seed()
    return _ok(order_svc.kds_board)


@app.get("/api/sales/today")
def sales_today():
    _need_seed()
    return _ok(cash_svc.day_report)


@app.get("/api/shift")
def get_shift():
    _need_seed()
    return _ok(cash_svc.current_shift)


@app.post("/api/shift/open")
def open_shift(body: OpenShiftIn):
    _need_seed()
    return _ok(cash_svc.open_shift, body.opening_cash_cents)


@app.post("/api/shift/close")
def close_shift(body: CloseShiftIn):
    _need_seed()
    return _ok(cash_svc.close_shift, body.counted_cash_cents)


@app.get("/api/orders/{order_id}/balance")
def order_balance(order_id: int):
    _need_seed()
    return _ok(cash_svc.order_balance, order_id)


@app.post("/api/orders/{order_id}/pay")
def pay_order(order_id: int, body: PayIn):
    _need_seed()
    return _ok(cash_svc.pay_order, order_id, body.method, body.amount_cents, body.tip_cents)


@app.post("/api/orders/{order_id}/refund")
def refund_order(order_id: int):
    _need_seed()
    return _ok(cash_svc.refund_order, order_id)
