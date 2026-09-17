from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.mechanisms import mechanism_for
from app.profiles import PROFILES, resolve_modules
from app.seed import ensure_demo_venue
from app.serializers import product_out, space_out, station_out
from app.settings import settings


def current_profile() -> str:
    profile = settings.hermes_profile.strip().lower()
    return profile if profile in PROFILES else "restaurant"


def instance_payload(seed: dict | None = None) -> dict:
    profile = current_profile()
    modules = resolve_modules(profile, settings.hermes_modules)
    mech = mechanism_for(profile)
    payload = {
        "name": settings.app_name,
        "env": settings.app_env,
        "profile": profile,
        "profile_label": PROFILES[profile]["label"],
        "modules": modules,
        "mechanism": mech,
        "tagline": "El mensaje llega.",
        "database": bool(settings.database_url),
    }
    if seed and seed.get("venue"):
        payload["venue"] = {
            "id": seed["venue"]["id"],
            "name": seed["venue"]["name"],
            "slug": seed["venue"]["slug"],
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
        ensure_demo_venue()
    except Exception as exc:  # noqa: BLE001 — boot should not die without DB
        print(f"hermes: seed skipped ({exc})")
    yield


app = FastAPI(title="Hermes OS", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "name": settings.app_name}


@app.get("/api/instance")
def instance():
    try:
        seed = ensure_demo_venue()
    except Exception:
        seed = None
    return instance_payload(seed)


@app.get("/api/spaces")
def list_spaces():
    seed = _need_seed()
    return [space_out(s) for s in seed["spaces"]]


@app.get("/api/stations")
def list_stations():
    seed = _need_seed()
    return [station_out(s) for s in seed["stations"]]


@app.get("/api/products")
def list_products():
    seed = _need_seed()
    return [product_out(p) for p in seed["products"]]


def _need_seed() -> dict:
    try:
        seed = ensure_demo_venue()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {exc}") from exc
    if not seed:
        raise HTTPException(status_code=503, detail="DATABASE_URL no configurada")
    return seed
