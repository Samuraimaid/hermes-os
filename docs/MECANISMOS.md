# Mecanismos por rubro

El perfil no solo enciende módulos. Cambia **la unidad de trabajo**, **adónde viaja el pedido** y **cuándo se cobra**.

El código comparte las mismas tablas. Cambia la configuración del local.

## Unidad de trabajo

| Rubro | Unidad | Ejemplo |
|---|---|---|
| Restaurante | Mesa | Mesa 12, 4 cubiertos |
| Bar | Cuenta de barra | Taburete 3, “Juan”, barra corrida |
| Buffet | Paso / bandeja | Estación caliente, postres, caja de salida |
| Comida rápida | Turno de mostrador | Ticket 47, llamar al número |
| Convivencia | Ticket de caja | SKU + cantidad, entrega inmediata |

En base de datos eso es un `space` con `kind` distinto (`table`, `tab`, `line`, `queue`, `counter`). No son cinco productos.

## Cómo viaja el pedido

| Rubro | Envío | Quién “bumpea” |
|---|---|---|
| Restaurante | Cada ítem a su estación (cocina o barra) | Cocinero / bartender, luego expedición |
| Bar | Ítems de trago a barra; comida a cocina si existe | Bartender |
| Buffet | Casi no hay comanda por mesa. La cocina **repondrá** la estación | Encargado de estación |
| Comida rápida | Un ticket entero a cocina → ventanilla | Cocina marca listo; mostrador entrega |
| Convivencia | No hay viaje. Se cobra y se entrega en el mismo acto | Cajero |

## Cuándo se cobra

| Rubro | Cobro |
|---|---|
| Restaurante | Después, al cerrar la mesa |
| Bar | Sobre la cuenta abierta, cuando el cliente se va (o por ronda) |
| Buffet | En la entrada (pago único) o en la salida, según el local |
| Comida rápida | En el mostrador, al pedir o al entregar |
| Convivencia | En el momento, en caja |

Hermes no mezcla “cerrar mesa” con “timbrar factura fiscal”. El cobro interno es el módulo `caja`. Lo fiscal es otra capa, por país.

## Carta

Un producto declara:

- si se vende en sala, barra o mostrador
- a qué estación de producción va (o a ninguna)
- si es ilimitado (buffet) o con stock

Así un jugo puede ir a barra en un restaurante y venderse en caja en una convivencia, sin duplicar el catálogo.

## Lo que viene después de este paso

1. Modelo persistente (este paso): venues, spaces, stations, products, orders.
2. API de carta y de espacios según el perfil.
3. Flujo de orden mínimo: abrir unidad → agregar ítems → enviar.
4. Recién entonces UI de mesero / mostrador / KDS.
