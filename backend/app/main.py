from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.profiles import PROFILES, resolve_modules
from app.settings import settings

app = FastAPI(title="Hermes OS", version="0.1.0")
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
    profile = settings.hermes_profile.strip().lower()
    if profile not in PROFILES:
        profile = "restaurant"
    modules = resolve_modules(profile, settings.hermes_modules)
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "profile": profile,
        "profile_label": PROFILES[profile]["label"],
        "modules": modules,
        "tagline": "El mensaje llega.",
    }
