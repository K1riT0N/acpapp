// Create an account (prototype: vSignup). Adds a password field, which the prototype didn't need.
import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";

import { ErrorText } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { loginHref, useAfterLogin, useAuth } from "@/lib/auth";
import { baht, CATEGORIES } from "@/lib/format";

export default function Signup() {
  const router = useRouter();
  const toast = useToast();
  const { signIn } = useAuth();
  const afterLogin = useAfterLogin();
  const { data: plans } = useApi("/plans");
  const [f, setF] = useState({
    role: "customer", full_name: "", email: "", phone: "", password: "",
    shop_name: "", category: CATEGORIES[0], address: "", line: true,
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const owner = f.role === "shop_owner";
  const free = plans?.find((p) => p.plan_id === "free");
  const pro = plans?.find((p) => p.plan_id === "pro");

  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await api("/auth/register", { method: "POST", body: f });
      if (result.user.role === "shop_owner") {
        signIn(result);
        toast("Shop created. Add your first service so customers can book.");
        router.push("/owner/services");
      } else {
        afterLogin(result);
      }
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <form className="panel" onSubmit={submit} noValidate>
        <h1>Create an account</h1>
        <div className="seg" role="group" aria-label="Account type">
          <button type="button" aria-pressed={!owner} onClick={() => { setF({ ...f, role: "customer" }); setError(""); }}>
            I&apos;m booking
          </button>
          <button type="button" aria-pressed={owner} onClick={() => { setF({ ...f, role: "shop_owner" }); setError(""); }}>
            I run a shop
          </button>
        </div>
        <div className="field">
          <label htmlFor="su-name">Your name</label>
          <input id="su-name" autoComplete="name" value={f.full_name} onChange={set("full_name")} />
        </div>
        <div className="two">
          <div className="field">
            <label htmlFor="su-email">Email</label>
            <input id="su-email" type="email" autoComplete="email" value={f.email} onChange={set("email")} />
          </div>
          <div className="field">
            <label htmlFor="su-phone">Phone</label>
            <input id="su-phone" type="tel" autoComplete="tel" value={f.phone} onChange={set("phone")} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="su-pass">Password (at least 8 characters)</label>
          <input id="su-pass" type="password" autoComplete="new-password" value={f.password} onChange={set("password")} />
        </div>
        {owner && (
          <>
            <div className="field">
              <label htmlFor="su-shop">Shop name</label>
              <input id="su-shop" value={f.shop_name} onChange={set("shop_name")} />
            </div>
            <div className="two">
              <div className="field">
                <label htmlFor="su-cat">Type of shop</label>
                <select id="su-cat" value={f.category} onChange={set("category")}>
                  {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="su-addr">Area or address</label>
                <input id="su-addr" value={f.address} onChange={set("address")} />
              </div>
            </div>
          </>
        )}
        <label className="check">
          <input type="checkbox" id="su-line" checked={f.line} onChange={set("line")} />
          <span>Send my alerts and reminders on LINE</span>
        </label>
        <div className="mt"><ErrorText error={error} /></div>
        <button className="btn primary wide" type="submit" disabled={busy}>
          {owner ? "Create account and shop" : "Create account"}
        </button>
        <p className="fine">Prototype: don&apos;t reuse a password you use on other sites.</p>
        <p className="t-meta mt-s">
          Already have an account? <Link href={loginHref(typeof router.query.next === "string" ? router.query.next : "")}>Log in</Link>
        </p>
      </form>

      <div className="side-copy">
        {owner ? (
          <>
            <h2>For shop owners</h2>
            <p>
              Your shop gets a public page customers can find. Every booking comes with a deposit, so a no-show costs you
              less, and you get a LINE alert the moment a customer books.
            </p>
            {free && pro && (
              <p>
                The Free plan covers {free.booking_limit} bookings a month. Pro removes the limit for {baht(pro.monthly_price)} a month.
              </p>
            )}
          </>
        ) : (
          <>
            <h2>For customers</h2>
            <p>
              Book a time in under a minute, pay a small deposit by PromptPay, and get a reminder before you go. You pay the
              rest at the shop.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
