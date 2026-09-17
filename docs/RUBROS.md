# Rubros (perfiles)

El perfil solo elige módulos por defecto y etiquetas. No ramifica el código en cinco productos.

| Perfil | Clave | Módulos por defecto |
|---|---|---|
| Restaurante | `restaurant` | sala, cocina, caja, pantallas |
| Bar | `bar` | barra, cocina, caja, pantallas |
| Buffet | `buffet` | mostrador, cocina, caja, pantallas |
| Comida rápida | `qsr` | mostrador, cocina, caja, pantallas |
| Convivencia | `convenience` | mostrador, caja, pantallas |

Se puede mezclar. Ejemplo: un local que es restaurante de día y bar de noche:

```env
HERMES_PROFILE=restaurant
HERMES_MODULES=sala,barra,cocina,caja,pantallas
```

## Cómo se ve cada rubro

**Restaurante.** Unidad = mesa. El mesero envía; cocina marca listo.

**Bar.** Unidad = taburete o cuenta de barra. Tickets cortos. Estación de bartender.

**Buffet.** Unidad = bandeja / paso por caja. Pantallas de estación y de sala. Menos mapa de mesas.

**Comida rápida.** Unidad = turno en mostrador. Un flujo: pedir → producir → entregar.

**Convivencia.** Unidad = ticket de caja. Carta corta, antojitos, bebidas. Cocina opcional.

El detalle operativo (envío y cobro) está en `MECANISMOS.md`.
