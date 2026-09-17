import { useEffect, useState } from "react";

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/instance")
      .then((r) => {
        if (!r.ok) throw new Error("API no disponible");
        return r.json();
      })
      .then(setData)
      .catch(() => setError("No se pudo hablar con la API. ¿Está arriba el backend?"));
  }, []);

  return (
    <main className="shell">
      <div className="kicker">Plantilla de local</div>
      <h1>Hermes OS</h1>
      <p className="tag">{data?.tagline || "El mensaje llega."}</p>

      <section className="card">
        {error && <p className="err">{error}</p>}
        {!error && !data && <p>Cargando instancia…</p>}
        {data && (
          <>
            <div className="row">
              <span className="label">Nombre</span>
              <strong>{data.name}</strong>
            </div>
            <div className="row">
              <span className="label">Perfil</span>
              <strong>{data.profile_label}</strong>
            </div>
            <div className="row">
              <span className="label">Unidad</span>
              <strong>{data.mechanism?.order_unit}</strong>
            </div>
            <div className="row">
              <span className="label">Envío</span>
              <strong>{data.mechanism?.fulfillment}</strong>
            </div>
            <div className="row">
              <span className="label">Cobro</span>
              <strong>{data.mechanism?.payment}</strong>
            </div>
            <div className="row">
              <span className="label">Despliegue</span>
              <strong>{data.deployment?.label || "Local"}</strong>
            </div>
            <p className="summary">{data.mechanism?.summary}</p>
            {data.deployment?.summary && (
              <p className="summary">{data.deployment.summary}</p>
            )}
            <div className="pills">
              {(data.modules || []).map((m) => (
                <span className="pill" key={m}>
                  {m}
                </span>
              ))}
            </div>
          </>
        )}
      </section>

      <p className="foot">Cambia HERMES_PROFILE para ver otro rubro. La carta y los espacios se crean al arrancar.</p>
    </main>
  );
}
