// Free or Pro (prototype: vPlan): upgrade with a test PromptPay payment, or switch back to Free.
import { useState } from "react";

import FakeQR from "@/components/FakeQR";
import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { baht, fmtDateLong, fmtDT, METHOD, monthName, todayStr } from "@/lib/format";
import { useMessages } from "@/lib/messages";

function Plan() {
  const toast = useToast();
  const { user } = useAuth();
  const { reload: reloadMessages } = useMessages();
  const { data, error, setData } = useApi("/owner/plan");
  const [upgrading, setUpgrading] = useState(false);
  const [confirmFree, setConfirmFree] = useState(false);
  const [busy, setBusy] = useState(false);

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!data) return <Loading />;

  const free = data.plans.find((p) => p.plan_id === "free");
  const pro = data.plans.find((p) => p.plan_id === "pro");
  const isPro = data.plan.plan_id === "pro";
  const t = todayStr();

  async function change(path, message) {
    setBusy(true);
    try {
      setData(await api(`/owner/plan/${path}`, { method: "POST" }));
      setUpgrading(false);
      setConfirmFree(false);
      toast(message);
      reloadMessages();
    } catch (e) {
      toast(e.message);
    }
    setBusy(false);
  }

  let action;
  if (isPro && confirmFree) {
    action = (
      <div className="warnbox">
        <p>Switch to Free now? Pro ends today, and you&apos;re limited to {free.booking_limit} bookings a month again.</p>
        <div className="row">
          <button className="btn danger small" disabled={busy} onClick={() => change("downgrade", "You're on the Free plan now.")}>
            Switch to Free
          </button>
          <button className="btn small" onClick={() => setConfirmFree(false)}>Stay on Pro</button>
        </div>
      </div>
    );
  } else if (isPro) {
    action = (
      <>
        <p>
          Pro is active until {fmtDateLong(data.subscription?.end_date || t)}. After that the shop moves back to Free unless you pay
          for another month.
        </p>
        <button className="btn small mt-s" onClick={() => setConfirmFree(true)}>Switch to Free now</button>
      </>
    );
  } else if (upgrading) {
    action = (
      <div className="pay-inline">
        <FakeQR seed={"pro-" + user.shop_id} small />
        <div>
          <h3>Pay for one month of Pro</h3>
          <p className="amount">{baht(pro.monthly_price)}</p>
          <p className="fine">PromptPay test mode, so no real money moves.</p>
          <div className="row mt-s">
            <button className="btn primary" disabled={busy} onClick={() => change("upgrade", "You're on Pro now.")}>
              Simulate successful payment
            </button>
            <button className="btn link" onClick={() => setUpgrading(false)}>Not now</button>
          </div>
        </div>
      </div>
    );
  } else {
    action = (
      <>
        <p>{data.usage.used} of {free.booking_limit} bookings used in {monthName(t)}.</p>
        <button className="btn accent" onClick={() => setUpgrading(true)}>Upgrade to Pro</button>
      </>
    );
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Plan</h1>
          <p className="lede">Free covers a small shop. Pro removes the monthly booking limit.</p>
        </div>
      </div>
      <div className="plans">
        <div className={"plan" + (!isPro ? " current" : "")}>
          <h2>Free</h2>
          <p className="p-price">{baht(0)}<small> a month</small></p>
          <p>Up to {free.booking_limit} bookings a month.</p>
          <p className="t-meta">Shop page, deposits and reminders included.</p>
          {!isPro && <p className="mt-s"><span className="chip">Your plan</span></p>}
        </div>
        <div className={"plan" + (isPro ? " current" : "")}>
          <h2>Pro</h2>
          <p className="p-price">{baht(pro.monthly_price)}<small> a month</small></p>
          <p>Unlimited bookings.</p>
          <p className="t-meta">Everything in Free.</p>
          {isPro && <p className="mt-s"><span className="chip ok">Your plan</span></p>}
        </div>
      </div>
      <div className="panel mt">{action}</div>
      <section>
        <h2>Plan payments</h2>
        {data.payments.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Date</th><th>Plan</th><th>Method</th><th>Reference</th><th className="num">Amount</th></tr>
              </thead>
              <tbody>
                {data.payments.map((p) => (
                  <tr key={p.payment_id}>
                    <td>{fmtDT(p.paid_at)}</td>
                    <td>{p.plan_name}</td>
                    <td>{METHOD[p.method] || p.method}</td>
                    <td>{p.gateway_ref || ""}</td>
                    <td className="num">{baht(p.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty">No plan payments yet.</p>
        )}
      </section>
    </>
  );
}

export default function PlanPage() {
  return (
    <RequireRole role="shop_owner" message="Log in to manage your shop.">
      <Plan />
    </RequireRole>
  );
}
