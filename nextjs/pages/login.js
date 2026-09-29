// Log in page (prototype: vLogin), with the list of demo accounts.
import Link from "next/link";
import { useState } from "react";

import { ErrorText } from "@/components/States";
import { api, useApi } from "@/lib/api";
import { useAfterLogin } from "@/lib/auth";
import { DEMO_PASSWORD } from "@/lib/format";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const afterLogin = useAfterLogin();
  const { data: demo } = useApi("/auth/demo-accounts");

  async function logIn(email, password) {
    setBusy(true);
    setError("");
    try {
      afterLogin(await api("/auth/login", { method: "POST", body: { email, password } }));
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  function submit(e) {
    e.preventDefault();
    logIn(form.email, form.password);
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="auth">
      <form className="panel" onSubmit={submit} noValidate>
        <h1>Log in</h1>
        <div className="field">
          <label htmlFor="le">Email</label>
          <input id="le" type="email" autoComplete="username" value={form.email} onChange={set("email")} />
        </div>
        <div className="field">
          <label htmlFor="lp">Password</label>
          <input id="lp" type="password" autoComplete="current-password" value={form.password} onChange={set("password")} />
        </div>
        <ErrorText error={error} />
        <button className="btn primary wide" type="submit" disabled={busy}>Log in</button>
        <p className="t-meta mt">
          New here? <Link href="/signup">Create an account</Link>
        </p>
      </form>

      {demo && demo.length > 0 && (
        <div className="panel">
          <h2>Demo accounts</h2>
          <p className="t-meta">
            Every demo account uses the password <code>{DEMO_PASSWORD}</code>. Try a customer and a shop owner side by side.
          </p>
          {demo.map((d) => (
            <div className="demo-row" key={d.user_id}>
              <div>
                <strong>{d.full_name}</strong>
                <p className="t-meta">
                  {d.role === "customer"
                    ? "Customer"
                    : "Owner of " + (d.shop_name || "a shop") + (d.shop_name ? " (" + d.plan_name + ")" : "")}
                  . {d.email}
                </p>
              </div>
              <button className="btn small" disabled={busy} onClick={() => logIn(d.email, DEMO_PASSWORD)}>
                Log in
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
