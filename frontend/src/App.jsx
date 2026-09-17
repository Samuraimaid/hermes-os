import { useCallback, useEffect, useState } from "react";

async function api(path, opts = {}) {
  const token = localStorage.getItem("hermes_token");
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    localStorage.removeItem("hermes_token");
    localStorage.removeItem("hermes_user");
    throw new Error("No autorizado");
  }
  if (!res.ok) throw new Error(data.detail || "Error de API");
  return data;
}

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("hermes_user") || "null");
    } catch {
      return null;
    }
  });
  const [view, setView] = useState("piso");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");

  const caps = user?.caps || [];
  const canFloor = caps.includes("floor") || caps.includes("admin");
  const canKds = caps.includes("kds") || caps.includes("admin");
  const canCash = caps.includes("cash") || caps.includes("admin");
  const canKiosk = caps.includes("kiosk") || caps.includes("admin");

  async function enter() {
    try {
      setError("");
      const session = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({ pin }),
      });
      localStorage.setItem("hermes_token", session.token);
      localStorage.setItem("hermes_user", JSON.stringify(session));
      setUser(session);
      setView(
        session.caps.includes("kiosk") && !session.caps.includes("admin")
          ? "kiosko"
          : session.caps.includes("kds") && !session.caps.includes("floor")
            ? "kds"
            : session.caps.includes("cash") && !session.caps.includes("floor")
              ? "caja"
              : "piso"
      );
    } catch (e) {
      setError(e.message);
    }
  }

  function leave() {
    api("/api/logout", { method: "POST" }).catch(() => {});
    localStorage.removeItem("hermes_token");
    localStorage.removeItem("hermes_user");
    setUser(null);
    setPin("");
  }

  if (!user) {
    return (
      <main className="shell">
        <div className="kicker">Hermes OS</div>
        <h1>Entrar</h1>
        <p className="tag">PIN demo: 0000 dueño · 1111 mesero · 2222 cocina · 3333 caja · 4444 kiosco</p>
        {error && <p className="err">{error}</p>}
        <input className="field" value={pin} onChange={(e) => setPin(e.target.value)} placeholder="PIN" />
        <button className="primary" onClick={enter}>
          Entrar
        </button>
      </main>
    );
  }

  return (
    <main className="shell wide">
      <div className="kicker">Hermes OS · {user.name} · {user.role}</div>
      <h1>Hermes OS</h1>
      <div className="tabs">
        {canFloor && (
          <button className={view === "piso" ? "tab on" : "tab"} onClick={() => setView("piso")}>
            Piso
          </button>
        )}
        {canKds && (
          <button className={view === "kds" ? "tab on" : "tab"} onClick={() => setView("kds")}>
            Estaciones
          </button>
        )}
        {canCash && (
          <button className={view === "caja" ? "tab on" : "tab"} onClick={() => setView("caja")}>
            Caja
          </button>
        )}
        {canKiosk && (
          <button className={view === "kiosko" ? "tab on" : "tab"} onClick={() => setView("kiosko")}>
            Kiosco
          </button>
        )}
        <button className="tab" onClick={leave}>
          Salir
        </button>
      </div>
      {view === "piso" && canFloor && <FloorView />}
      {view === "kds" && canKds && <KdsView />}
      {view === "caja" && canCash && <CashView />}
      {view === "kiosko" && canKiosk && <KioskView />}
    </main>
  );
}

function FloorView() {
  const [instance, setInstance] = useState(null);
  const [spaces, setSpaces] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [current, setCurrent] = useState(null);
  const [pending, setPending] = useState(null);
  const [picked, setPicked] = useState([]);
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
                onClick={() => {
                  if (p.modifiers && p.modifiers.length) {
                    setPending(p);
                    setPicked([]);
                    return;
                  }
                  run(async () => {
                    const order = await api(`/api/orders/${current.id}/items`, {
                      method: "POST",
                      body: JSON.stringify({ product_id: p.id, qty: 1 }),
                    });
                    setCurrent(order);
                  });
                }}
              >
                <strong>{p.name}</strong>
                <span>{p.station || "caja"} · {(p.price_cents / 100).toFixed(2)}</span>
              </button>
            ))}
          </div>
          {pending && (
            <div className="ticket">
              <p>
                <strong>{pending.name}</strong>
              </p>
              {pending.modifiers.map((m) => (
                <label key={m.id} className="muted" style={{ display: "block", marginTop: 6 }}>
                  <input
                    type="checkbox"
                    checked={picked.includes(m.id)}
                    onChange={() =>
                      setPicked(
                        picked.includes(m.id) ? picked.filter((id) => id !== m.id) : [...picked, m.id]
                      )
                    }
                  />{" "}
                  {m.name}
                  {m.price_delta_cents ? ` (+${(m.price_delta_cents / 100).toFixed(2)})` : ""}
                </label>
              ))}
              <button
                className="primary"
                onClick={() =>
                  run(async () => {
                    const order = await api(`/api/orders/${current.id}/items`, {
                      method: "POST",
                      body: JSON.stringify({
                        product_id: pending.id,
                        qty: 1,
                        modifier_ids: picked,
                      }),
                    });
                    setCurrent(order);
                    setPending(null);
                    setPicked([]);
                  })
                }
              >
                Agregar
              </button>
            </div>
          )}
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
                      {i.modifiers?.length
                        ? ` (${i.modifiers.map((m) => m.name).join(", ")})`
                        : ""}
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
                {t.modifiers?.length ? (
                  <p className="muted">{t.modifiers.map((m) => m.name).join(" · ")}</p>
                ) : null}
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
  const [payAmt, setPayAmt] = useState({});
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
            {orders.map((o) => {
              const due = o.due_cents ?? o.precuenta.subtotal_cents;
              const typed = payAmt[o.id];
              const amount = typed === undefined ? money(due) : typed;
              return (
              <div className="ticket" key={o.id}>
                <header>
                  <strong>
                    {o.space?.name || `#${o.id}`} · {o.status}
                  </strong>
                  <span>
                    pagado {money(o.paid_cents)} · falta {money(due)}
                  </span>
                </header>
                <input
                  className="field"
                  value={amount}
                  onChange={(e) => setPayAmt({ ...payAmt, [o.id]: e.target.value })}
                />
                <div className="actions">
                  {[2, 3].map((n) => (
                    <button
                      key={n}
                      className="tab"
                      onClick={() =>
                        setPayAmt({ ...payAmt, [o.id]: money(Math.ceil(due / n)) })
                      }
                    >
                      1/{n}
                    </button>
                  ))}
                  <button className="tab" onClick={() => setPayAmt({ ...payAmt, [o.id]: money(due) })}>
                    Todo
                  </button>
                </div>
                <div className="actions">
                  {["cash", "card", "transfer"].map((m) => (
                    <button
                      key={m}
                      className="rowbtn"
                      onClick={() =>
                        run(async () => {
                          const cents = Math.round(Number(amount) * 100);
                          if (!cents) throw new Error("Indica un monto");
                          const tip_cents = Math.round((cents * tipPct) / 100);
                          await api(`/api/orders/${o.id}/pay`, {
                            method: "POST",
                            body: JSON.stringify({
                              method: m,
                              amount_cents: cents,
                              tip_cents,
                            }),
                          });
                          setPayAmt((prev) => {
                            const next = { ...prev };
                            delete next[o.id];
                            return next;
                          });
                        })
                      }
                    >
                      {m === "cash" ? "Efectivo" : m === "card" ? "Tarjeta" : "Transfer"}
                    </button>
                  ))}
                </div>
              </div>
              );
            })}
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

function KioskView() {
  const [products, setProducts] = useState([]);
  const [space, setSpace] = useState(null);
  const [cart, setCart] = useState([]);
  const [option, setOption] = useState("dine_in");
  const [pending, setPending] = useState(null);
  const [picked, setPicked] = useState([]);
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/api/products"), api("/api/spaces")])
      .then(([pr, sp]) => {
        setProducts(pr);
        setSpace(sp.find((s) => s.kind === "kiosk") || sp.find((s) => s.kind === "queue") || sp[0]);
      })
      .catch((e) => setError(e.message));
  }, []);

  function addLine(product, modifierIds) {
    const mods = (product.modifiers || []).filter((m) => modifierIds.includes(m.id));
    const extra = mods.reduce((n, m) => n + (m.price_delta_cents || 0), 0);
    setCart([
      ...cart,
      {
        key: `${product.id}-${Date.now()}`,
        product_id: product.id,
        name: product.name,
        price_cents: product.price_cents + extra,
        modifier_ids: modifierIds,
        modifiers: mods,
      },
    ]);
    setPending(null);
    setPicked([]);
  }

  async function place() {
    try {
      setError("");
      if (!space) throw new Error("No hay kiosco configurado");
      if (!cart.length) throw new Error("Elige algo de la carta");
      const order = await api("/api/orders", {
        method: "POST",
        body: JSON.stringify({ space_id: space.id, dining_option: option }),
      });
      for (const line of cart) {
        await api(`/api/orders/${order.id}/items`, {
          method: "POST",
          body: JSON.stringify({
            product_id: line.product_id,
            qty: 1,
            modifier_ids: line.modifier_ids,
          }),
        });
      }
      const sent = await api(`/api/orders/${order.id}/send`, { method: "POST" });
      setTicket(sent);
      setCart([]);
    } catch (e) {
      setError(e.message);
    }
  }

  const total = cart.reduce((n, l) => n + l.price_cents, 0);

  if (ticket) {
    return (
      <section className="card">
        <h2>Pedido recibido</h2>
        <p className="tag" style={{ fontSize: 42, margin: "12px 0" }}>
          {ticket.queue_number ? `Turno ${ticket.queue_number}` : `Pedido #${ticket.id}`}
        </p>
        <p className="muted">Pasa a recoger cuando llamen tu número.</p>
        <button className="primary" onClick={() => setTicket(null)}>
          Nuevo pedido
        </button>
      </section>
    );
  }

  return (
    <>
      <p className="tag">Pide aquí. Pagas en caja o al recoger, según el local.</p>
      {error && <p className="err">{error}</p>}
      <div className="actions" style={{ marginBottom: 16 }}>
        <button className={option === "dine_in" ? "tab on" : "tab"} onClick={() => setOption("dine_in")}>
          Comer aquí
        </button>
        <button className={option === "takeout" ? "tab on" : "tab"} onClick={() => setOption("takeout")}>
          Para llevar
        </button>
      </div>
      <div className="grid">
        <section className="card">
          <h2>Carta</h2>
          {products.map((p) => (
            <button
              key={p.id}
              className="rowbtn"
              onClick={() => {
                if (p.modifiers?.length) {
                  setPending(p);
                  setPicked([]);
                } else addLine(p, []);
              }}
            >
              <strong>{p.name}</strong>
              <span>{money(p.price_cents)}</span>
            </button>
          ))}
          {pending && (
            <div className="ticket">
              <strong>{pending.name}</strong>
              {pending.modifiers.map((m) => (
                <label key={m.id} className="muted" style={{ display: "block", marginTop: 6 }}>
                  <input
                    type="checkbox"
                    checked={picked.includes(m.id)}
                    onChange={() =>
                      setPicked(picked.includes(m.id) ? picked.filter((id) => id !== m.id) : [...picked, m.id])
                    }
                  />{" "}
                  {m.name}
                </label>
              ))}
              <button className="primary" onClick={() => addLine(pending, picked)}>
                Sumar
              </button>
            </div>
          )}
        </section>
        <section className="card">
          <h2>Tu pedido</h2>
          {cart.length === 0 && <p className="muted">Vacío</p>}
          {cart.map((l) => (
            <div className="row" key={l.key}>
              <span>
                {l.name}
                {l.modifiers.length ? ` (${l.modifiers.map((m) => m.name).join(", ")})` : ""}
              </span>
              <span>{money(l.price_cents)}</span>
            </div>
          ))}
          <p className="summary">Total {money(total)}</p>
          <button className="primary" disabled={!cart.length} onClick={place}>
            Enviar pedido
          </button>
        </section>
      </div>
    </>
  );
}
