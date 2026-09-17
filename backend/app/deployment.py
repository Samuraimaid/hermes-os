"""Where the venue brain lives."""

from __future__ import annotations

MODES = {
    "local": {
        "label": "Local",
        "brain": "PC del local",
        "devices": "LAN o Wi-Fi del negocio",
        "without_venue_internet": "El servicio sigue",
        "without_venue_power": "Se apaga, salvo UPS",
        "remote_billing": False,
        "summary": "El cerebro está en el local. No depende de internet del barrio.",
    },
    "cloud": {
        "label": "Nube",
        "brain": "API y base hospedadas",
        "devices": "Wi-Fi o datos móviles (4G/5G)",
        "without_venue_internet": "Si no hay datos en el dispositivo, se corta",
        "without_venue_power": "Celulares con batería y datos pueden seguir",
        "remote_billing": True,
        "summary": "Sin PC en el local. El dueño ve facturación en remoto. Los dispositivos salen por 4G si no quieren Wi-Fi.",
    },
    "hybrid": {
        "label": "Híbrido",
        "brain": "Copia local + réplica en la nube",
        "devices": "LAN primero; nube de respaldo y de consulta",
        "without_venue_internet": "El piso sigue en local; el remoto se atrasará",
        "without_venue_power": "El piso se apaga; el dueño aún ve el último sync",
        "remote_billing": True,
        "summary": "El servicio no se cae con el barrio. El dueño consulta ventas y cortes desde fuera.",
    },
}


def resolve_deployment(raw: str | None) -> str:
    key = (raw or "local").strip().lower()
    return key if key in MODES else "local"


def deployment_for(raw: str | None) -> dict:
    key = resolve_deployment(raw)
    payload = dict(MODES[key])
    payload["mode"] = key
    return payload
