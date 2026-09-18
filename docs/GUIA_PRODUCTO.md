# Guía de producto Hermes OS

Qué queremos construir. Inspirado en el TPV + KDS + CDS + Dashboard y en la *Guía del usuario* (feb 2023), para **uso interno**. No es un clone de Play Store: mismos conceptos y nombres, código y marca propios.

Fuentes de esta guía: POS 2.74, Dashboard 1.13, KDS 1.9, CDS 1.8 y el manual ES.

## Cuatro caras (como ellos)

| Cara | En Loyverse | En Hermes | Estado |
|---|---|---|---|
| TPV / Ventas | app POS | Piso + Caja + Kiosco | Parcial |
| Cocina | app KDS | Estaciones | Parcial |
| Pantalla cliente | app CDS | módulo `pantallas` | No |
| Back office | Dashboard / web | pestaña Ventas + Artículos + Configuración | No |

Un hub web está bien para el molde. En un local: tablet TPV, tablet cocina, tablet cliente, PC dueño — mismas APIs.

## Nombres obligatorios (UI en español)

| Usar | No usar |
|---|---|
| Artículo | Producto (en UI) |
| Ticket (abierto) | Orden (en UI) |
| Recibo (ya cobrado) | Factura (eso es fiscal) |
| Turno | “Caja del turno” como título largo |
| Empleado | Staff / usuario |
| Tienda | Venue (solo en código) |
| Iniciar sesión | Entrar |
| Modificador | Extra suelto |
| Tipo de pedido | dining_option en UI |
| Resumen de ventas | Dashboard genérico |
| Inventario bajo / Agotado | stock vacío informal |
| Reembolso | void de cobro |
| Descuento | promo |
| Impuesto | IVA metido en precio sin decirlo |

Código puede seguir `product`, `order`, `shift`. La pantalla habla como el manual.

## Mapa del manual → Hermes

### Ya cubierto (no rehacer)

- Tienda + perfil (`HERMES_PROFILE`)
- Artículos demo + categorías + precio
- Modificadores en el renglón (falta grupo / obligatorio)
- Ticket abierto por mesa o taburete
- Tickets predefinidos = nuestros `spaces` (Mesa 1…)
- Combinar tickets (`merge`) y mover renglones (`move`)
- Enviar a estación / KDS con bump prep → ready
- Ítem anulado no se mueve; si hay pagos no se mueve
- KDS ve modificadores; artículo anulado debería tacharse (falta rojo)
- Tipo de pedido en kiosco (comer aquí / para llevar)
- Dividir pago por monto + propina %
- Turno: abrir, esperado, contado, diferencia
- Empleado + PIN + caps
- Kiosco (ellos no lo traen igual; nosotros sí)

### Núcleo TPV que falta (prioridad)

1. **Pantalla de ventas** tipo ticket | carta  
   Carta por categoría/páginas. Ticket a un lado. Cobrar abajo.  
2. **Descuento** en ticket o renglón (% o monto).  
3. **Impuesto** añadido o incluido; no es factura fiscal.  
4. **Reembolso** sobre un recibo (cap dueño/cajero).  
5. **Anular renglón** (`void`) y que KDS lo tache en rojo.  
6. **Tipos de pedido** en piso, no solo kiosco.  
7. **Lista de recibos** del turno.  
8. **Dividir ticket** por renglones (hoy solo por monto).

### KDS (de la app 1.9 + cap. 9.19–9.21)

- Tablet apaisada, estación filtrada  
- Color por tiempo: aviso / tarde (segundos configurables)  
- Sonido al llegar ticket  
- Done = bump ready  
- Recall = recuperar last done (opcional)  
- Voided se ve tachado  
- Misma red; poll está bien  
- No hace falta app nativa todavía: ruta `/kds` a pantalla completa

### CDS (app 1.8 + cap. 6.13–6.14 y 9.22–9.23)

- Segunda pantalla: artículos del ticket, subtotal, descuentos, total  
- En cobro: elegir propina (0 / % / monto)  
- Gracias + total pagado  
- Ruta `/cds` a pantalla completa; TPV no muestra esa UI al cliente

### Back office / Dashboard (app 1.13 + cap. 7)

Tres pestañas, dueño:

- **Ventas:** resumen (brutas, netas, descuentos, impuestos, propinas, reembolsos, total cobrado), venta promedio, recibos  
- **Artículos:** alta, categoría, precio, modificadores, stock bajo  
- **Configuración:** tienda, impuestos, descuentos, empleados, PIN, tipos de pedido, tema

### Inventario (cap. 4) — después

SKU, stock, compra, ajuste, recuento, compuesto/receta. Convivencia y buffet lo necesitan antes que un fine dining.

### Empleados extra (cap. 5)

Reloj checador, cambiar empleado sin salir, grupos de permisos finos. El PIN actual alcanza para v1.

### Clientes / lealtad (cap. 6) — satélite

Ficha, puntos, recibo por email. No bloquea operar.

### Hardware (cap. 9) — satélite

Impresora recibo, impresora cocina, escáner, cajón. El molde imprime PDF/HTML primero.

### Pagos con datáfono (cap. 10) — satélite

Efectivo / tarjeta / transfer manual ya existen. SumUp/Zettle no van en el núcleo.

### Offline (2.21) = `HERMES_DEPLOYMENT=hybrid`

Vender y abrir turno sin nube; sync después. No está implementado.

## Pantallas Hermes objetivo

```
Iniciar sesión (PIN)
├── Ventas (TPV)     floor + cash juntos en restaurant/qsr
│     ticket | artículos | cobrar
├── Tickets abiertos / Mapa de mesas
├── Estaciones (KDS)
├── Kiosco
├── Pantalla cliente (CDS)
├── Turno
└── Back office (dueño)
      Ventas | Artículos | Configuración
```

## Qué no entra en el núcleo

- Logo o nombre Loyverse  
- Suscripciones, marketplace, API de ellos  
- Datáfonos de terceros  
- Factura de Hacienda (conector aparte)  
- Reloj checador e inventario avanzado en el primer corte operable

## Orden de construcción (close-loop)

1. Renombrar UI a esta nomenclatura — hecho  
2. Temas CSS por perfil (`docs/TEMAS.md`) — default del perfil hecho  
3. Pantalla Ventas ticket | carta | cobrar — hecho (void en el mismo corte)  
4. Void de renglón + KDS tachado + colores de tiempo — hecho (`/kds`, aviso 5 min / tarde 10 min)  
5. Ruta CDS mínima — hecho (artículos, subtotal, total; sin propina)  
6. Descuento + impuesto (ticket interno)  
7. Back office: resumen de ventas + lista de artículos  
8. Reembolso y lista de recibos  
9. Inventario SKU si el rubro lo pide  
10. Hybrid / impresora / CDS propina

## Prueba de aceptación (local operable)

Mesero `1111`: abre Mesa 1, agrega artículo + modificador, envía.  
Cocina `2222`: ve ticket, bump.  
Cajero `3333`: parte pago, propina, cierra turno.  
Dueño `0000`: ve resumen del turno.  
Kiosco `4444`: turno numerado.  
Si hay pagos, Mover/Juntar fallan.
