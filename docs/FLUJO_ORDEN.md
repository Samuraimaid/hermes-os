# Flujo de orden (0.3)

Una orden nace en una **unidad** del rubro (mesa, taburete, turno, línea o caja), no en el aire.

## Pasos

1. `POST /api/orders` `{ space_id, cover_count?, dining_option? }`
   - Si esa unidad ya tiene una orden activa, la reabre.
   - Comida rápida asigna `queue_number`.
2. `POST /api/orders/{id}/items` `{ product_id, qty, notes? }`
   - El ítem hereda la estación del producto.
   - No se vende en un origen que el producto no permita.
3. `POST /api/orders/{id}/send`
   - `fire_items_to_stations` / `counter_then_expo`: el ítem queda en cola de la estación.
   - `direct_handover` (convivencia): se marca servido al instante.
   - `replenish_display_stations` (buffet): registra consumo de isla, no una comanda de mesa.
4. `GET /api/stations/{key}/tickets` — lo que ve cocina o barra.
5. `POST /api/items/{id}/bump` `{ action: prep | ready | served }`
6. `POST /api/orders/{id}/deliver` — todo listo; sale a sala. Falla si cocina sigue con cola.
7. `POST /api/orders/{id}/close` — sale de la pista. **No cobra.** Solo si está lista o entregada.

`GET /api/orders/{id}` no hace falta: el cuerpo de cada POST ya trae la orden y su **precuenta**.

## Dining option

`dine_in` | `takeout` | `delivery`. No cambia las tablas; cambia la etiqueta del ticket.


## Pantalla de estaciones

`GET /api/kds` agrupa los tickets por estación de producción.

En el hub, pestaña **Estaciones**. El cocinero pasa `queued → prep → ready`.
La vista se refresca cada 4 segundos. No hace falta WebSocket todavía.
