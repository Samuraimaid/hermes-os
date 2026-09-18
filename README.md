# Hermes OS

Plantilla de operación para un local que vende comida o bebida.

Un molde. Muchos locales. Cada instalación lleva su marca, su carta y solo los módulos que necesita.

> El mensaje llega.

## Qué es

Hermes OS no es el sistema de un solo negocio. Es una base que se adapta a:

| Rubro | Perfil |
|---|---|
| Restaurante de mesa | `restaurant` |
| Bar | `bar` |
| Buffet | `buffet` |
| Comida rápida | `qsr` |
| Tienda de convivencia / abarrotes con comida | `convenience` |

Los módulos se encienden o se apagan por cliente:

- **Sala** — mesas y servicio en piso
- **Barra** — tickets de bebidas y cuentas de barra
- **Cocina** — pantalla de producción (KDS)
- **Mostrador** — venta rápida de balcón
- **Pantallas** — carta y publicidad en displays
- **Caja** — cobro, ticket, corte de turno

La facturación fiscal (Hacienda, DGI, SAT u otra autoridad) no forma parte del núcleo. Se agrega por país cuando el cliente la exige.

## Stack

| Capa | Tecnología |
|---|---|
| API | FastAPI + WebSockets |
| App | React + Vite |
| Datos | PostgreSQL 16 |
| Arranque | Docker Compose |

## Continuar en otro chat (VS Code / Grok)

Lee `GROK.md` y `docs/CONTEXTO.md`. Ahí está el hilo, las decisiones y el siguiente paso.

## Arranque

```bash
cp .env.example .env
docker compose up --build
```

- App: http://localhost:5173
- API: http://localhost:8000
- Salud: http://localhost:8000/health
- Docs: http://localhost:8000/docs

Sin Docker, el backend y el frontend también pueden correr por separado (ver `docs/DESARROLLO.md`).

## Perfil de un local

En `.env`:

```env
HERMES_PROFILE=bar
HERMES_MODULES=barra,cocina,caja,pantallas
```

Despliegue (`HERMES_DEPLOYMENT`): `local`, `cloud` o `hybrid`. Tablets por 4G y consulta remota de facturación sin Wi‑Fi del local. Ver `docs/DESPLIEGUE.md`.

Si `HERMES_MODULES` va vacío, Hermes usa los módulos por defecto de ese perfil.

El perfil también cambia el **mecanismo**: unidad de trabajo (mesa, cuenta, turno, línea, caja), cómo viaja el pedido y cuándo se cobra. Ver `docs/MECANISMOS.md`.

Cambia `HERMES_PROFILE` y vuelve a levantar. El seed crea espacios, estaciones y una carta genérica de ese rubro.

## Estructura

```
hermes-os/
├── backend/          API
├── frontend/         Apps de sala, caja, cocina y pantallas
├── db/init/          Esquema inicial
├── docs/             Producto y operación
├── docker-compose.yml
└── .env.example
```

## Estado

Núcleo 0.3: orden + precuenta + KDS + caja + mapa de mesas (mover/juntar).
