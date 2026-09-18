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
8. `POST /api/items/{id}/move` `{ to_space_id }` — el renglón cambia de cuenta. Si el destino no tiene orden abierta, se crea. Conserva status y `sent_at`; cocina no recibe un ticket nuevo.
9. `POST /api/orders/{id}/merge` `{ onto_order_id }` — todos los ítems vivos pasan a la otra cuenta.
10. `POST /api/items/{id}/void` — anula el renglón. Falla si hay pagos. Si no quedan ítems vivos, cierra el ticket. Cap `floor`.
11. `GET /api/cds` — ticket activo para la pantalla cliente (sin PIN). Sin órdenes abiertas, `ticket: null`.

Mover y juntar fallan si origen o destino ya tienen pagos. Recalculan el status de ambas; si el origen queda vacío, se cierra (libera la mesa). Solo entre espacios `table` o `tab`. Cap `floor`.

`GET /api/orders/{id}` no hace falta: el cuerpo de cada POST ya trae la orden y su **precuenta**. Move y merge devuelven `{ source, destination }`.

## Dining option

`dine_in` | `takeout` | `delivery`. No cambia las tablas; cambia la etiqueta del ticket.


## Pantalla de estaciones

`GET /api/kds` agrupa los tickets por estación de producción.

Ruta `/kds`: pantalla completa, apaisada. Si no hay sesión, pide PIN y queda en `/kds`.
El cocinero pasa `queued → prep → ready`. Poll 4 s. Aviso a los 5 min (`--hermes-accent`), tarde a los 10 (`--hermes-late`). Void tachado. Sin sonido ni Recall.

En **Ventas**, restaurante y bar ven el mapa en una franja. Debajo: ticket | artículos. Enviar va en el ticket. Cobrar (barra inferior) solo con cap `cash`. Un renglón anulado se tacha en el ticket y en KDS.
