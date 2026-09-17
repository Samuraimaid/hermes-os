# Referencia: sistemas citados en el comparador de Siigo

Fuente: artículo “Software para restaurantes en Colombia”. No son plantillas a clonar. Son listas de trabajo.

## 1. Siigo POS Gastrobar

Qué es: TPV en la nube de un ecosistema **contable** colombiano.

Sirve mirar: precuenta, mesas, comandas a cocina/barra, turnos de caja, propinas, combos, partir cuenta, inventario, reportes, factura electrónica DIAN (CUFE + QR).

No copiar: DIAN como núcleo, ni “todo vive solo en la nube”. Siigo vende cumplimiento fiscal + contabilidad. Hermes vende operación del local; lo fiscal es conector.

## 2. Loggro Restobar

Qué es: TPV nube para resto/bar. Distingue **documento POS** (ticket de venta) de **factura electrónica**, y permite convertir uno en el otro después.

Sirve mirar:

- Pedir y cobrar **con o sin internet** (offline del dispositivo).
- Carta QR por mesa.
- Roles (mesero ≠ cajero).
- Integración Rappi / domicilios como canal, no como producto entero.
- Mapear medios de pago locales a códigos de la autoridad fiscal.

Idea fuerte para Hermes: **ticket interno primero, comprobante legal después**. Exactamente la separación caja ≠ fiscal.

## 3. SoftRestaurant

Qué es: el más cercano a lo que queremos ser. Tiene edición **que funciona sin internet** y edición **Cloud**. CFDI / autofactura según país. Recetas, explosión de insumos, mapa de mesas, comandero móvil, monitor de cocina, corte por WhatsApp, multi-sucursal.

Sirve mirar:

- Dos ediciones (local y nube), no una religión.
- Autofactura: el cliente genera el comprobante en casa con un token del ticket.
- Recetas y costeo (fase posterior).
- Tiempos en el mapa de mesas (cuánto lleva abierta).

SoftRestaurant 12 “funciona incluso sin internet” + SoftRestaurant Cloud es el espejo de `local` + `cloud` en Hermes.

## 4. Carbonara Manager / Carbonara App

Qué es (en la práctica actual): **lista de espera y reservas**, no un TPV de facturación. Mapa de mesas para sentar, SMS/WhatsApp, depósitos, no-show.

Sirve mirar más adelante: waitlist y reservas como módulo opcional de sala. No entra al núcleo de caja ni de cocina.

El artículo de Siigo lo mezcla con POS. En Hermes no se mezcla.

## 5. Oracle GloriaFood

Qué es: canal digital. Pedidos web ilimitados sin comisión, menú online, para llevar / domicilio, reservas, pre-order. POS ligero de Oracle, no un fiscalizador.

Sirve mirar: un `origin=online` que cae en la misma cola de cocina. Menú que se edita una vez y sale en sala y en web. Agotados. Eso es módulo de canal, fase tardía.

## Qué nos quedamos

| Idea | De quién | Dónde en Hermes |
|---|---|---|
| Ticket POS ≠ factura legal | Loggro | `caja` + conector fiscal |
| Local y nube como ediciones | SoftRestaurant | `HERMES_DEPLOYMENT` |
| Offline del dispositivo + sync | Loggro, GloriaFood | modo `hybrid` |
| Precuenta, propina, split | Siigo / tabla | flujo de sala/bar |
| Autofactura del cliente | SoftRestaurant | conector fiscal |
| Carta QR / pedidos web | Loggro, GloriaFood | canal, no núcleo |
| Reservas y waitlist | Carbonara, GloriaFood | módulo opcional de sala |
| Recetas y merma | SoftRestaurant, Siigo | inventario, después |

Nada de esto obliga a un proveedor de nube concreto ni a la DIAN.
