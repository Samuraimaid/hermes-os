# Modificadores

Opciones de un producto: sin hielo, doble, término, extra salsa.

Se eligen al agregar el ítem. El precio del renglón es precio base + deltas. Cocina ve los nombres en el ticket.

`POST /api/orders/{id}/items` `{ product_id, qty, modifier_ids: [1, 2] }`
