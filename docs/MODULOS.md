# Módulos

Cada módulo es un interruptor. El núcleo (locales, usuarios, carta, estaciones) siempre está.

| Clave | Nombre | Para qué |
|---|---|---|
| `sala` | Sala | Mesas, cuentas abiertas, meseros |
| `barra` | Barra | Tickets cortos, modificadores de bebida, KDS de bartender |
| `cocina` | Cocina | Pantalla de producción, estados, tiempos |
| `mostrador` | Mostrador | Venta rápida, una cuenta, sin mesa |
| `pantallas` | Pantallas | Carta y publicidad en displays |
| `caja` | Caja | Medios de pago, ticket interno, corte |

## Dependencias

- `sala` y `barra` pueden vivir juntas en el mismo local.
- `cocina` tiene sentido si hay estación de producción.
- `mostrador` reemplaza o convive con `sala` (comida rápida).
- `caja` es independiente: se puede operar un tiempo solo con comandas y cobrar afuera.
- `pantallas` no exige caja ni mesas.

## Contrato mínimo de una orden

Toda orden, viva en mesa o en mostrador, guarda:

- origen (sala, barra, mostrador)
- estación destino por ítem (cocina, barra, ninguno)
- estado por ítem y por orden
- notas y modificadores
- marca de tiempo al enviar, al iniciar y al listar como listo
