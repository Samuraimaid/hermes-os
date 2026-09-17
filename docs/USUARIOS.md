# Usuarios y roles

PIN de 4 dígitos. No es un sistema de nómina.

## Roles demo (se crean al arrancar)

| Nombre | Rol | PIN | Ve |
|---|---|---|---|
| Dueño | `owner` | `0000` | Todo |
| Mesero | `waiter` | `1111` | Piso |
| Cocina | `kitchen` | `2222` | Estaciones |
| Cajero | `cashier` | `3333` | Caja y cuentas |

Cámbialos en un local real. Estos PIN son de plantilla.

## API

- `POST /api/login` `{ pin }` → `{ token, name, role, caps }`
- Header: `Authorization: Bearer <token>`
- `POST /api/logout`

Caps: `floor` · `kds` · `cash` · `admin`.
