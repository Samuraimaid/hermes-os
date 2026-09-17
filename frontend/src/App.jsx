import { useCallback, useEffect, useState } from "react";

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Error de API");
  return data;
}

export default function App() {
  const [view, setView] = useState("piso");
  return (
    <main className="shell wide">
      <div className="kicker">Hermes OS</div>
      <h1>Hermes OS</h1>
      <div className="tabs">
        <button className={view === "piso" ? "tab on" : "tab"} onClick={() => setView("piso")}>
          Piso
        </button>
        <button className={view === "kds" ? "tab on" : "tab"} onClick={() => setView("kds")}>
          Estaciones
        </button>
        <button className={view === "caja" ? "tab on" : "tab"} onClick={() => setView("caja")}>
          Caja
        </button>
      </div>
      {view === "piso" ? <FloorView /> : view === "kds" ? <KdsView /> : <CashView />}
    </main>
  );
}

function FloorView() {
  const [instance, setInstance] = useState(null);
  const [spaces, setSpaces] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [current, setCurrent] = useState(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [inst, sp, pr, ords] = await Promise.all([
      api("/api/instance"),
      api("/api/spaces"),
      api("/api/products"),
      api("/api/orders"),
    ]);
    setInstance(inst);
    setSpaces(sp);
    setProducts(pr);
    setOrders(ords);
    setCurrent((prev) => ords.find((o) => o.id === prev?.id) || prev);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, [refresh]);

  async function run(fn) {
    try {
      setError("");
      await fn();
      await refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <p className="tag">
        {instance
          ? `${instance.profile_label} · ${instance.mechanism?.order_unit} · ${instance.deployment?.label || ""}`
          : "El mensaje llega."}
      </p>
      {error && <p className="err">{error}</p>}
      <div className="grid">
        <section className="card">
          <h2>Unidades</h2>
          <div className="list">
            {spaces.map((s) => (
              <button
                key={s.id}
                className="rowbtn"
                onClick={() =>
                  run(async () => {
                    const order = await api("/api/orders", {
                      method: "POST",
                      body: JSON.stringify({ space_id: s.id, cover_count: 2 }),
                    });
                    setCurrent(order);
                  })
                }
              >
                <strong>{s.name}</strong>
                <span>{s.kind}</span>
              </button>
            ))}
          </div>
        </section>
        <section className="card">
          <h2>Carta</h2>
          <div className="list">
            {products.map((p) => (
              <button
                key={p.id}
                className="rowbtn"
                disabled={!current}
                onClick={() =>
                  run(async () => {
                    const order = await api(`/api/orders/${current.id}/items`, {
                      method: "POST",
                      body: JSON.stringify({ product_id: p.id, qty: 1 }),
                    });
                    setCurrent(order);
                  })
                }
              >
                <strong>{p.name}</strong>
                <span>{p.station || "caja"} · {(p.price_cents / 100).toFixed(2)}</span>
              </button>
            ))}
          </div>
        </section>
        <section className="card">
          <h2>{current ? current.space?.name || `Orden #${current.id}` : "Orden"}</h2>
          {!current && <p className="muted">Abre una unidad para empezar.</p>}
          {current && (
            <>
              <p className="muted">
                {current.status} · {current.origin}
                {current.queue_number ? ` · turno ${current.queue_number}` : ""}
              </p>
              <div className="list">
                {current.items.map((i) => (
                  <div className="row" key={i.id}>
                    <span>
                      {i.qty}× {i.name}
                    </span>
                    <span>
                      {i.station || "—"} · {i.status}
                    </span>
                  </div>
                ))}
              </div>
              <p className="summary">
                Precuenta: {(current.precuenta.subtotal_cents / 100).toFixed(2)} ·{" "}
                {current.precuenta.item_count} ítems
              </p>
              <button
                className="primary"
                onClick={() =>
                  run(async () => {
                    const order = await api(`/api/orders/${current.id}/send`, { method: "POST" });
                    setCurrent(order);
                  })
                }
              >
                Enviar
              </button>
              {(current.status === "ready" || current.status === "delivered") && (
                <button
                  className="rowbtn"
                  onClick={() =>
                    run(async () => {
                      const order = await api(`/api/orders/${current.id}/deliver`, { method: "POST" });
                      setCurrent(order);
                    })
                  }
                >
                  Entregar
                </button>
              )}
              {(current.status === "ready" || current.status === "delivered") && (
                <button
                  className="primary"
                  onClick={() =>
                    run(async () => {
                      const order = await api(`/api/orders/${current.id}/close`, { method: "POST" });
                      setCurrent(order);
                    })
                  }
                >
                  Cerrar pista
                </button>
              )}
            </>
          )}
        </section>
      </div>
      <section className="card" style={{ marginTop: 18 }}>
        <h2>Abiertas ahora</h2>
        {orders.length === 0 && <p className="muted">Nadie en pista.</p>}
        {orders.map((o) => (
          <button key={o.id} className="rowbtn" onClick={() => setCurrent(o)}>
            <strong>
              {o.space?.name || `#${o.id}`} · {o.status}
            </strong>
            <span>{o.precuenta.item_count} ítems</span>
          </button>
        ))}
      </section>
    </>
  );
}

function KdsView() {
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setBoard(await api("/api/kds"));
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
    const id = setInterval(() => refresh().catch(() => {}), 4000);
    return () => clearInterval(id);
  }, [refresh]);

  async function bump(itemId, action) {
    try {
      setError("");
      await api(`/api/items/${itemId}/bump`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      await refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  const mode = board?.kitchen_mode;
  const emptyHint =
    mode === "none"
      ? "Este rubro no manda tickets a estación. Se entrega en caja."
      : mode === "replenish"
        ? "El buffet repone islas; no hay comanda por mesa."
        : "Nada en cola. Envía desde Piso.";

  return (
    <>
      <p className="tag">Lo que ve cocina o barra. Se actualiza solo.</p>
      {error && <p className="err">{error}</p>}
      {!board && <p className="muted">Cargando estaciones…</p>}
      {board && board.stations.length === 0 && <p className="muted">{emptyHint}</p>}
      <div className="grid">
        {(board?.stations || []).map((st) => (
          <section className="card kds" key={st.key}>
            <h2>
              {st.name} <span className="muted">{st.kind}</span>
            </h2>
            {st.tickets.length === 0 && <p className="muted">Sin tickets</p>}
            {st.tickets.map((t) => (
              <article className={`ticket ${t.status}`} key={t.item_id}>
                <header>
                  <strong>
                    {t.qty}× {t.name}
                  </strong>
                  <span>{t.space || (t.queue_number ? `Turno ${t.queue_number}` : `#${t.order_id}`)}</span>
                </header>
                {t.notes && <p className="muted">{t.notes}</p>}
                <div className="actions">
                  {t.status === "queued" && (
                    <button className="rowbtn" onClick={() => bump(t.item_id, "prep")}>
                      En prep
                    </button>
                  )}
                  {t.status === "prep" && (
                    <button className="primary" onClick={() => bump(t.item_id, "ready")}>
                      Listo
                    </button>
                  )}
                </div>
              </article>
            ))}
          </section>
        ))}
      </div>
    </>
  );
}

function money(cents) {
  return ((cents || 0) / 100).toFixed(2);
}

function CashView() {
  const [shift, setShift] = useState(null);
  const [orders, setOrders] = useState([]);
  const [opening, setOpening] = useState("0");
  const [counted, setCounted] = useState("0");
  const [tipPct, setTipPct] = useState(0);
  const [error, setError] = useState("");
  const [closed, setClosed] = useState(null);

  async function refresh() {
    const [sh, ords] = await Promise.all([api("/api/shift"), api("/api/orders")]);
    setShift(sh);
    setOrders(ords);
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  async function run(fn) {
    try {
      setError("");
      await fn();
      await refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <p className="tag">Turno de caja. Ticket interno, no factura fiscal.</p>
      {error && <p className="err">{error}</p>}
      {!shift && (
        <section className="card">
          <h2>Abrir turno</h2>
          <p className="muted">Fondo inicial en efectivo</p>
          <input className="field" value={opening} onChange={(e) => setOpening(e.target.value)} />
          <button
            className="primary"
            onClick={() =>
              run(async () => {
                await api("/api/shift/open", {
                  method: "POST",
                  body: JSON.stringify({ opening_cash_cents: Math.round(Number(opening) * 100) }),
                });
              })
            }
          >
            Abrir caja
          </button>
        </section>
      )}
      {shift && (
        <>
          <section className="card">
            <h2>Turno #{shift.id}</h2>
            <div className="row">
              <span className="label">Fondo</span>
              <strong>{money(shift.opening_cash_cents)}</strong>
            </div>
            <div className="row">
              <span className="label">Ventas</span>
              <strong>{money(shift.totals.sales_cents)}</strong>
            </div>
            <div className="row">
              <span className="label">Efectivo esperado</span>
              <strong>{money(shift.totals.expected_cash_cents)}</strong>
            </div>
            <div className="row">
              <span className="label">Propinas</span>
              <strong>{money(shift.totals.tips_cents)}</strong>
            </div>
            <p className="muted">
              Efectivo {money(shift.totals.by_method.cash)} · Tarjeta {money(shift.totals.by_method.card)} ·
              Transfer {money(shift.totals.by_method.transfer)}
            </p>
          </section>
          <section className="card" style={{ marginTop: 18 }}>
            <h2>Cobrar órdenes abiertas</h2>
            <p className="muted">Propina que se suma al cobrar</p>
            <div className="actions">
              {[0, 10, 15].map((n) => (
                <button
                  key={n}
                  className={tipPct === n ? "tab on" : "tab"}
                  onClick={() => setTipPct(n)}
                >
                  {n}%
                </button>
              ))}
            </div>
            {orders.length === 0 && <p className="muted">No hay cuentas en pista.</p>}
            {orders.map((o) => (
              <div className="ticket" key={o.id}>
                <header>
                  <strong>
                    {o.space?.name || `#${o.id}`} · {o.status}
                  </strong>
                  <span>{money(o.precuenta.subtotal_cents)}</span>
                </header>
                <div className="actions">
                  {["cash", "card", "transfer"].map((m) => (
                    <button
                      key={m}
                      className="rowbtn"
                      onClick={() =>
                        run(async () => {
                          const bal = await api(`/api/orders/${o.id}/balance`);
                          if (!bal.due_cents) throw new Error("Ya está pagada");
                          const tip_cents = Math.round((bal.due_cents * tipPct) / 100);
                          await api(`/api/orders/${o.id}/pay`, {
                            method: "POST",
                            body: JSON.stringify({
                              method: m,
                              amount_cents: bal.due_cents,
                              tip_cents,
                            }),
                          });
                        })
                      }
                    >
                      {m === "cash" ? "Efectivo" : m === "card" ? "Tarjeta" : "Transfer"}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </section>
          <section className="card" style={{ marginTop: 18 }}>
            <h2>Cerrar turno</h2>
            <p className="muted">Efectivo contado en el cajón</p>
            <input className="field" value={counted} onChange={(e) => setCounted(e.target.value)} />
            <button
              className="primary"
              onClick={() =>
                run(async () => {
                  const out = await api("/api/shift/close", {
                    method: "POST",
                    body: JSON.stringify({ counted_cash_cents: Math.round(Number(counted) * 100) }),
                  });
                  setClosed(out);
                })
              }
            >
              Cerrar caja
            </button>
          </section>
        </>
      )}
      {closed && (
        <p className="summary">
          Diferencia: {money(closed.totals.difference_cents)} (contado menos esperado)
        </p>
      )}
    </>
  );
}
