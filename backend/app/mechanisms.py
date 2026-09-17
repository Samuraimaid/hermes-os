"""How each venue profile actually operates.

Profiles pick modules. Mechanisms pick the unit of work, how an order
travels, and when money is collected. Same tables, different rules.
"""

from __future__ import annotations

MECHANISMS: dict[str, dict] = {
    "restaurant": {
        "order_unit": "table",
        "space_kind": "table",
        "fulfillment": "fire_items_to_stations",
        "payment": "pay_after",
        "needs_cover_count": True,
        "needs_queue_number": False,
        "kitchen_mode": "tickets",
        "typical_spaces": "Mesas numeradas por zona (salón, terraza).",
        "typical_stations": "Cocina caliente, fríos, expedición. Barra si hay tragos.",
        "summary": "El mesero abre una mesa, manda ítems a estaciones y cobra al cerrar.",
    },
    "bar": {
        "order_unit": "tab",
        "space_kind": "tab",
        "fulfillment": "fire_items_to_stations",
        "payment": "pay_tab",
        "needs_cover_count": False,
        "needs_queue_number": False,
        "kitchen_mode": "tickets",
        "typical_spaces": "Taburetes, barra corrida o cuentas con nombre.",
        "typical_stations": "Estación de bartender. Cocina solo si hay comida de barra.",
        "summary": "Cuentas cortas, modificadores de bebida, cobro sobre la cuenta abierta.",
    },
    "buffet": {
        "order_unit": "line",
        "space_kind": "line",
        "fulfillment": "replenish_display_stations",
        "payment": "pay_at_pass",
        "needs_cover_count": True,
        "needs_queue_number": False,
        "kitchen_mode": "replenish",
        "typical_spaces": "Líneas o islas del buffet, no mesas de comanda.",
        "typical_stations": "Islas calientes, frías, postres. Caja de entrada o salida.",
        "summary": "La cocina repone estaciones. El cliente no genera un ticket por plato.",
    },
    "qsr": {
        "order_unit": "queue",
        "space_kind": "queue",
        "fulfillment": "counter_then_expo",
        "payment": "pay_at_counter",
        "needs_cover_count": False,
        "needs_queue_number": True,
        "kitchen_mode": "tickets",
        "typical_spaces": "Un mostrador y una cola de turnos.",
        "typical_stations": "Cocina + ventanilla de entrega. Número de turno visible.",
        "summary": "Se pide en mostrador, se produce el ticket completo y se llama el número.",
    },
    "convenience": {
        "order_unit": "counter",
        "space_kind": "counter",
        "fulfillment": "direct_handover",
        "payment": "pay_at_counter",
        "needs_cover_count": False,
        "needs_queue_number": False,
        "kitchen_mode": "none",
        "typical_spaces": "Una o más cajas.",
        "typical_stations": "Sin cocina, salvo antojitos opcionales.",
        "summary": "Cobro inmediato por SKU. No hay viaje a producción.",
    },
}


def mechanism_for(profile: str) -> dict:
    return MECHANISMS.get(profile, MECHANISMS["restaurant"])
