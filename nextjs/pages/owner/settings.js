// Shop details, deposit rate and opening hours (prototype: vSettings).
import { useEffect, useState } from "react";

import RequireRole from "@/components/RequireRole";
import { ErrorText, Loading } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { CATEGORIES, DOW, WEEK } from "@/lib/format";

// Turn the API's shop into the form's fields; each day gets open_1, from_1, to_1, cap_1 ...
function toForm(shop) {
  const f = {
    shop_name: shop.shop_name, category: shop.category || CATEGORIES[0], address: shop.address, phone: shop.phone,
    description: shop.description, deposit_percent: String(shop.deposit_percent),
  };
  WEEK.forEach((d) => {
    const h = shop.hours.find((x) => x.day_of_week === d);
    f["open_" + d] = !!h;
    f["from_" + d] = h ? h.open_time : "10:00";
    f["to_" + d] = h ? h.close_time : "19:00";
    f["cap_" + d] = String(h ? h.max_per_slot : 2);
  });
  return f;
}

function Settings() {
  const toast = useToast();
  const { data: shop, error } = useApi("/owner/shop");
  const [f, setF] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (shop && !f) setF(toForm(shop));
  }, [shop, f]);

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!f) return <Loading />;

  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const cats = CATEGORIES.includes(f.category) ? CATEGORIES : [...CATEGORIES, f.category];

  // Details and hours are two API calls. Both run, and any error messages are shown together.
  async function save() {
    setBusy(true);
    const errors = [];
    try {
      await api("/owner/shop", {
        method: "PATCH",
        body: {
          shop_name: f.shop_name, category: f.category, address: f.address, phone: f.phone, description: f.description,
          deposit_percent: f.deposit_percent === "" ? null : Number(f.deposit_percent),
        },
      });
    } catch (e) {
      errors.push(e.message);
    }
    try {
      await api("/owner/shop/hours", {
        method: "PUT",
        body: WEEK.map((d) => ({
          day_of_week: d, open: f["open_" + d], open_time: f["from_" + d], close_time: f["to_" + d],
          max_per_slot: f["cap_" + d] === "" ? null : Number(f["cap_" + d]),
        })),
      });
    } catch (e) {
      errors.push(e.message);
    }
    setErr(errors.join(" "));
    setBusy(false);
    if (!errors.length) toast("Shop settings saved.");
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Shop settings</h1>
          <p className="lede">What customers see on your page, your deposit rate, and when you take bookings.</p>
        </div>
      </div>
      <div className="grid-2 settings-grid">
        <section className="panel">
          <h2>Shop details</h2>
          <div className="field">
            <label htmlFor="st-name">Shop name</label>
            <input id="st-name" value={f.shop_name} onChange={set("shop_name")} />
          </div>
          <div className="two">
            <div className="field">
              <label htmlFor="st-cat">Type of shop</label>
              <select id="st-cat" value={f.category} onChange={set("category")}>
                {cats.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="st-phone">Phone</label>
              <input id="st-phone" type="tel" value={f.phone} onChange={set("phone")} />
            </div>
          </div>
          <div className="field">
            <label htmlFor="st-addr">Address</label>
            <input id="st-addr" value={f.address} onChange={set("address")} />
          </div>
          <div className="field">
            <label htmlFor="st-desc">Description</label>
            <textarea id="st-desc" value={f.description} onChange={set("description")} />
          </div>
          <div className="field">
            <label htmlFor="st-dep">Deposit (% of the service price)</label>
            <input id="st-dep" type="number" min="0" max="100" step="5" value={f.deposit_percent} onChange={set("deposit_percent")} />
          </div>
          <p className="fine">
            Deposits aren&apos;t refunded when a customer cancels or doesn&apos;t show up. Customers agree to this before they pay.
          </p>
        </section>

        <section className="panel">
          <h2>Opening hours</h2>
          <div className="hrow hhead">
            <span>Day</span><span>Opens</span><span>Closes</span><span>Customers at once</span>
          </div>
          {WEEK.map((d) => {
            const o = f["open_" + d];
            return (
              <div className="hrow" key={d}>
                <label className="check">
                  <input type="checkbox" id={"o" + d} checked={o} onChange={set("open_" + d)} />
                  <span>{DOW[d]}</span>
                </label>
                <input type="time" id={"f" + d} aria-label={DOW[d] + " opening time"} value={f["from_" + d]} onChange={set("from_" + d)} disabled={!o} />
                <input type="time" id={"t" + d} aria-label={DOW[d] + " closing time"} value={f["to_" + d]} onChange={set("to_" + d)} disabled={!o} />
                <input type="number" id={"c" + d} min="1" max="50" aria-label={DOW[d] + " customers at once"} value={f["cap_" + d]} onChange={set("cap_" + d)} disabled={!o} />
              </div>
            );
          })}
          <p className="fine">
            &quot;Customers at once&quot; is how many people you can serve in the same time slot, for example the number of chairs
            or bays.
          </p>
        </section>
      </div>
      <div className="mt">
        <ErrorText error={err} />
        <button className="btn primary" onClick={save} disabled={busy}>Save shop settings</button>
      </div>
    </>
  );
}

export default function SettingsPage() {
  return (
    <RequireRole role="shop_owner" message="Log in to manage your shop.">
      <Settings />
    </RequireRole>
  );
}
