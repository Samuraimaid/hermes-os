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
      </div>
      {view === "piso" ? <FloorView /> : <KdsView />}
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
