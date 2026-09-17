# Despliegue: local, nube e híbrido

Hermes no elige una sola casa. El cliente elige **dónde vive el cerebro** y **por qué red hablan los dispositivos**.

## Lo que la nube no hace

Si en el local no hay luz **y** los teléfonos están muertos, no opera nadie. La nube no inventa energía.

Lo que sí permite:

- El PC del local se apagó o no quieren montar servidor → las tablets usan **datos móviles (4G/5G)** contra la API hospedada.
- No quieren Wi‑Fi del local (inestable, no quieren abrir puertos) → mismo caso: red celular o la red de la casa del dueño.
- El dueño está en otro lado y quiere ver ventas, cortes y facturas → panel remoto sobre la copia en la nube.

## Tres modos

| Modo | `HERMES_DEPLOYMENT` | Cerebro | Los dispositivos | Si se cae internet del local | Si se va la luz del local |
|---|---|---|---|---|---|
| Local | `local` | PC + Docker + Postgres en el negocio | LAN / Wi‑Fi del local | El servicio **sigue** | Se apaga todo (salvo UPS) |
| Nube | `cloud` | API + base hospedadas | Wi‑Fi **o** 4G hacia internet | Se corta el servicio del local | Los celulares con batería y datos **pueden seguir** |
| Híbrido | `hybrid` | Copia local + réplica en la nube | LAN primero; nube de respaldo | El piso sigue en local; el dueño deja de ver el remoto hasta que sincronice | Igual que local, salvo que el dueño aún ve el último sync en la nube |

Recomendación de producto:

- Restaurante o bar con servicio largo y cocina → **híbrido** (el ticket no puede depender del barrio).
- Food truck, popup, convivencia chica, dueño que no quiere PC → **nube**.
- Local sin internet estable y con PC de siempre → **local**.

## Capas que no se mezclan

1. **Operación** — pedidos, estaciones, caja interna. Debe poder vivir en local.
2. **Espejo remoto** — el dueño mira ventas y cortes desde otro lado.
3. **Factura fiscal** — conector del país (DIAN, SAT, DGI…). Se engancha a la venta ya cerrada. No es el modo nube.

La nube de Hermes es para **acceder y, si se elige, operar**. No obliga a facturar en la nube de un tercero.

## Cómo se configura ahora

```env
HERMES_DEPLOYMENT=hybrid
```

Valores: `local` | `cloud` | `hybrid`.

Hoy el modo es un contrato de instancia. El hospedaje real (un VPS, un cluster) se arma por cliente; el código no asume un proveedor.
