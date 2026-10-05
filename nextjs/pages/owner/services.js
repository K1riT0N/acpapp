// The owner's services (prototype: vServices): edit, hide or show, and add new ones.
import { useState } from "react";

import RequireRole from "@/components/RequireRole";
import { ErrorText, Loading } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { baht, DURATIONS } from "@/lib/format";

// An empty price box is sent as null, so the API answers "Enter a price of 0 baht or more."
const toBody = (f) => ({
  service_name: f.name,
  price: f.price === "" ? null : Number(f.price),
  duration_min: Number(f.duration),
});

function DurationSelect({ id, value, onChange }) {
  return (
    <select id={id} value={value} onChange={onChange}>
      {DURATIONS.map((m) => <option key={m} value={String(m)}>{m} min</option>)}
    </select>
  );
}

function Services() {
  const toast = useToast();
  const { data: svcs, error, reload } = useApi("/owner/services");
  const [editId, setEditId] = useState(null);
  const [edit, setEdit] = useState({});
  const [editErr, setEditErr] = useState("");
  const [add, setAdd] = useState({ name: "", price: "", duration: "60" });
  const [addErr, setAddErr] = useState("");

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!svcs) return <Loading />;

  function startEdit(v) {
    setEditId(v.service_id);
    setEditErr("");
    setEdit({ name: v.service_name, price: String(v.price), duration: String(v.duration_min) });
  }

  async function save(id) {
    try {
      await api(`/owner/services/${id}`, { method: "PATCH", body: toBody(edit) });
      setEditId(null);
      await reload();
      toast("Service saved.");
    } catch (e) {
      setEditErr(e.message);
    }
  }

  async function toggle(v) {
    const on = !v.is_active;
    try {
      await api(`/owner/services/${v.service_id}`, { method: "PATCH", body: { is_active: on } });
      await reload();
      toast(on ? "Customers can book this again." : "Hidden from customers. Existing bookings stay.");
    } catch (e) {
      toast(e.message);
    }
  }

  async function addService() {
    try {
      await api("/owner/services", { method: "POST", body: toBody(add) });
      setAdd({ name: "", price: "", duration: "60" });
      setAddErr("");
      await reload();
      toast("Service added.");
    } catch (e) {
      setAddErr(e.message);
    }
  }

  const setE = (k) => (e) => setEdit({ ...edit, [k]: e.target.value });
  const setA = (k) => (e) => setAdd({ ...add, [k]: e.target.value });

  const rows = svcs.map((v) => {
    if (editId === v.service_id) {
      return (
        <div className="svc-edit" key={v.service_id}>
          <div className="field">
            <label htmlFor="es-name">Service name</label>
            <input id="es-name" value={edit.name} onChange={setE("name")} />
          </div>
          <div className="two">
            <div className="field">
              <label htmlFor="es-price">Price (฿)</label>
              <input id="es-price" type="number" min="0" step="10" value={edit.price} onChange={setE("price")} />
            </div>
            <div className="field">
              <label htmlFor="es-dur">Duration</label>
              <DurationSelect id="es-dur" value={edit.duration} onChange={setE("duration")} />
            </div>
          </div>
          <ErrorText error={editErr} />
          <div className="row">
            <button className="btn primary small" onClick={() => save(v.service_id)}>Save changes</button>
            <button className="btn small" onClick={() => { setEditId(null); setEditErr(""); }}>Cancel</button>
          </div>
        </div>
      );
    }
    return (
      <div className={"svc-row" + (v.is_active ? "" : " off")} key={v.service_id}>
        <div>
          <h3>{v.service_name}</h3>
          <p className="t-meta">{v.duration_min} min{v.is_active ? "" : ". Hidden from customers"}</p>
        </div>
        <span className="price">{baht(v.price)}</span>
        <div className="row">
          <button className="btn small" onClick={() => startEdit(v)}>Edit</button>
          <button className="btn small" onClick={() => toggle(v)}>{v.is_active ? "Hide" : "Show"}</button>
        </div>
      </div>
    );
  });

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Services</h1>
          <p className="lede">What customers can book. The duration sets how long each time slot is.</p>
        </div>
      </div>
      <div className="grid-2">
        <section>{svcs.length ? rows : <p className="empty">No services yet. Add one so customers can start booking.</p>}</section>
        <aside className="panel">
          <h2>Add a service</h2>
          <div className="field">
            <label htmlFor="ns-name">Service name</label>
            <input id="ns-name" placeholder="For example, Haircut" value={add.name} onChange={setA("name")} />
          </div>
          <div className="two">
            <div className="field">
              <label htmlFor="ns-price">Price (฿)</label>
              <input id="ns-price" type="number" min="0" step="10" value={add.price} onChange={setA("price")} />
            </div>
            <div className="field">
              <label htmlFor="ns-dur">Duration</label>
              <DurationSelect id="ns-dur" value={add.duration} onChange={setA("duration")} />
            </div>
          </div>
          <ErrorText error={addErr} />
          <button className="btn primary wide" onClick={addService}>Add service</button>
        </aside>
      </div>
    </>
  );
}

export default function ServicesPage() {
  return (
    <RequireRole role="shop_owner" message="Log in to manage your shop.">
      <Services />
    </RequireRole>
  );
}
