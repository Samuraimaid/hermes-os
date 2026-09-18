# Contexto e historial — Hermes OS

Documento para retomar el hilo en VS Code / Grok / cualquier chat nuevo.
No sustituye al código. Si este texto y el repo discrepan, gana el repo.

Última actualización del hilo original: 17 septiembre 2026.

## Qué se pidió al inicio (hilo limpio)

Empezar un producto **nuevo**, plantilla para cualquier local de comida o bebida. Se eligió el nombre **Hermes**. Trabajar en limpio: sin arrastrar un cliente anterior.

Referencias de mercado (ideas, no clones):

- Loyverse POS / loyverse.com — POS + KDS gratis; empleados e inventario como extra
- Artículo Siigo «Software para restaurantes» — Gastrobar, Loggro, SoftRestaurant, Carbonara, GloriaFood
- De ahí se guardó: ticket POS ≠ factura legal; local y nube como ediciones; precuenta, propina, split, roles

## Decisiones de producto

1. Un molde, muchos rubros. Configuración, no cinco codebases.
2. Perfil elige módulos por defecto **y** mecanismo (mesa vs cuenta vs turno vs línea vs caja).
3. Factura de Hacienda / DIAN / SAT / DGI **fuera del núcleo**.
4. Tres modos de despliegue: `local`, `cloud`, `hybrid`. La nube no inventa luz; sí permite tablets por 4G y ver ventas en remoto.
5. Token de sesión en memoria del API. Reiniciar el backend obliga a volver a entrar. Es plantilla, no SSO.
6. PIN demo de fábrica. Cambiarlos en un local real.

## Rubros y mecanismos

| Perfil | Unidad | Envío | Cobro |
|---|---|---|---|
| `restaurant` | mesa | ítem a estación | al cerrar |
| `bar` | cuenta / taburete | ítem a barra o cocina | sobre la cuenta |
| `buffet` | línea / isla | reponer estación | paso (entrada o salida) |
| `qsr` | turno | ticket a cocina → ventanilla | en mostrador |
| `convenience` | caja | entrega directa | en el acto |

Variable: `HERMES_PROFILE` y opcional `HERMES_MODULES`.
Despliegue: `HERMES_DEPLOYMENT=local|cloud|hybrid`.

## Qué hay construido

Orden de commits (rama `main`):

1. `6140c47` Plantilla FastAPI + React + Postgres + Docker
2. `6083e17` Esquema y mecanismos
3. `0a8f722` Modos local / nube / híbrido (contrato)
4. `208610a` Abrir unidad, ítems, enviar
5. `26fb000` KDS
6. `3ae206d` Entregar y cerrar pista
7. `f2007e8` Caja del turno
8. `c5c76e0` / `0f2f7e2` Propina en UI y en el cajón
9. `9c8afcd` Partir cuenta por monto
10. `f11c12a` Roles y PIN
11. `b2faed0` Modificadores
12. `53367dd` Kiosco de autoservicio
13. `6933d2f` Seed del kiosco: capacity como NULL
14. Mapa de mesas + mover/juntar ítems entre cuentas
15. Nomenclatura UI (GUIA_PRODUCTO) + tema CSS por perfil (TEMAS)
16. Ventas TPV (ticket | artículos | cobrar) + void de renglón
17. CDS: ruta `/cds` + `GET /api/cds`
18. KDS a pantalla completa `/kds` + color por tiempo
19. Descuento por cuenta (% o monto)
20. Back office mínimo: `/ventas` + `GET /api/sales/today`
21. Impuesto de tienda opcional (apagado por defecto, 1500 bps = 15%)
22. Moneda NIO/C$ y TPV compacto (franja de mesas)
23. Reembolso de recibo (no toca el ticket)
24. Tipografía TPV: Roboto 400/500/700, dinero tabular-nums
25. Configuración admin: moneda + IVA (`/config`)
26. Tipo de pedido en Ticket de piso (CDS/KDS)

### API útil

- `POST /api/login` `{ pin }`
- `GET /api/instance` `GET /api/spaces` `GET /api/products` `GET /api/orders`
- `POST /api/orders` `POST /api/orders/{id}/items` (`modifier_ids`) · `POST /api/orders/{id}/dining`
- `POST /api/orders/{id}/send` `/deliver` `/close` `/pay`
- `POST /api/items/{id}/move` `{ to_space_id }` · `POST /api/orders/{id}/merge` `{ onto_order_id }`
- `POST /api/items/{id}/void`
- `POST /api/orders/{id}/discount` `{ type, value }`
- `GET /api/cds` (sin PIN; ticket activo)
- `GET /api/sales/today` (cap `cash`) · `POST /api/venue/tax` `{ enabled, bps }`
- `POST /api/orders/{id}/refund` (cap `cash`)
- `GET /api/kds` `POST /api/items/{id}/bump`
- `GET|POST /api/shift` open/close

Caps: `floor` `kds` `cash` `kiosk` `admin`.
El rol `kiosk` puede pegarle a rutas de piso (para crear la orden). No cobra ni marca cocina.

### PIN demo

`0000` dueño · `1111` mesero · `2222` cocina · `3333` caja · `4444` kiosco

## Qué no está

- WebSocket (KDS y CDS hacen poll 4 s)
- Inventario / recetas
- Conector fiscal
- Offline real del modo híbrido (hoy es bandera + docs)
- Pantallas de publicidad / CDS propina
- App nativa
- Autofactura, Rappi, reservas

## Siguiente paso acordado

1. Catálogo de artículos en back office, o reembolso (`docs/GUIA_PRODUCTO.md`).
2. No empezar inventario ni factura legal hasta que el flujo diario no se rompa.

## Cómo pedirle a Grok en VS Code

Pegar o adjuntar `GROK.md` + este archivo. Frase útil:

> Continúa Hermes OS según GROK.md y docs/CONTEXTO.md. No reinicies el producto. El siguiente bloque es el que indique CONTEXTO, salvo que yo diga otra cosa.

## Notas sueltas del hilo

- SoftRestaurant (edición local + Cloud) es el espejo de `HERMES_DEPLOYMENT`.
- Loggro separa documento POS y factura electrónica: misma idea que caja vs fiscal.
- Carbonara y GloriaFood son satélites (reservas / canal web), no el TPV.
- Partir cuenta hoy es partir **monto**, no partir platos entre comensales.
- El kiosco no reutiliza la orden abierta de una mesa; siempre crea una nueva y da turno.
