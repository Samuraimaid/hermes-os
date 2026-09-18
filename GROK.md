# Instrucciones para Grok (continuar este repo)

Si abres este proyecto en VS Code u otro IDE, **lee este archivo y `docs/CONTEXTO.md` antes de tocar código.**

## Identidad del proyecto

- Nombre: **Hermes OS**
- Qué es: plantilla adaptable a restaurante, bar, buffet, comida rápida (`qsr`) y convivencia. No es el sistema de un solo cliente.
- Lema: «El mensaje llega.»
- Idioma de producto y docs: español. Código: inglés en identificadores, textos de UI en español.
- No reintroducir proyectos anteriores ni marcas de un local concreto.

## Cómo decidir

1. Misma base de tablas. El rubro cambia **mecanismo**, no el producto.
2. Caja interna ≠ factura fiscal. Lo fiscal es conector por país, después.
3. Local / nube / híbrido es **dónde vive el cerebro**, no otra app.
4. Un paso pequeño y comprobable. No mezclar cocina con cobro ni kiosco con mapa de mesas.
5. No clonar Loyverse, Siigo ni SoftRestaurant. Se usaron como checklist.

## Estado al cerrar el hilo original

Implementado hasta mapa de mesas y mover/juntar ítems:

- Perfiles + módulos + mecanismos
- Esquema Postgres, seed de local demo
- Flujo de orden, KDS, entregar, cerrar pista
- Caja de turno, propina, partir monto
- Roles y PIN
- Modificadores
- Kiosco de autoservicio
- Mapa de mesas (restaurant/bar) + `move` / `merge`

Siguiente paso: recorrer Piso con el mesero. No inventario ni factura fiscal.

## Arranque

```bash
cp .env.example .env
docker compose up --build
```

App `http://localhost:5173` · API `http://localhost:8000/docs`

PIN demo: `0000` dueño · `1111` mesero · `2222` cocina · `3333` caja · `4444` kiosco.

## Archivos que importan

| Ruta | Para qué |
|---|---|
| `docs/CONTEXTO.md` | Historial de decisiones de este chat |
| `docs/MECANISMOS.md` | Unidad, envío y cobro por rubro |
| `docs/DESPLIEGUE.md` | local / cloud / hybrid |
| `docs/FLUJO_ORDEN.md` | API de órdenes |
| `docs/CAJA.md` | Turno y pagos |
| `docs/USUARIOS.md` | Roles |
| `docs/MODIFICADORES.md` | Extras del ítem |
| `docs/KIOSCO.md` | Autoservicio |
| `backend/app/` | API |
| `frontend/src/App.jsx` | Hub (piso, KDS, caja, kiosco) |
