# Caja del turno

Cobra la precuenta. No emite factura fiscal.

## Flujo

1. `POST /api/shift/open` `{ opening_cash_cents }`
2. `POST /api/orders/{id}/pay` `{ method, amount_cents, tip_cents? }`
   - `method`: `cash` | `card` | `transfer` | `other`
   - Si se cubre el total, intenta entregar y cerrar la orden.
3. `POST /api/shift/close` `{ counted_cash_cents }`
   - Devuelve efectivo esperado (fondo + cobros en cash) y la diferencia.

`GET /api/shift` es el turno abierto o `null`.
`GET /api/orders/{id}/balance` dice cuánto falta.

Se puede partir el pago (efectivo + tarjeta) llamando `pay` dos veces.
