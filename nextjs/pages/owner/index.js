// The owner's dashboard (prototype: vDash): the week at a glance, the queue for a day, this month's usage
// and the latest alerts. Refreshes every 15 seconds.
import Link from "next/link";
import { useState } from "react";

import Meter from "@/components/Meter";
import OwnerActions from "@/components/OwnerActions";
import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import Ticket, { MsgLine } from "@/components/Ticket";
import { usePoll, useApi } from "@/lib/api";
import { DOW_S, fmtDateLong, fmtDT, monthName, parseDate, todayStr } from "@/lib/format";

function Dashboard() {
  const [day, setDay] = useState(null); // null = today
  const { data, error, reload } = useApi("/owner/dashboard" + (day ? `?date=${day}` : ""), { keepPrevious: true });
  usePoll(reload);

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!data) return <Loading />;

  const t = todayStr();
  const isPro = data.plan.plan_id === "pro";
  const u = data.usage;

  let usage;
  if (u.limit == null) {
    usage = (
      <>
        <h2>This month</h2>
        <p className="big-num">{u.used}</p>
        <p className="t-meta">Bookings in {monthName(t)}. You&apos;re on Pro, so there&apos;s no monthly limit.</p>
      </>
    );
  } else {
    const left = Math.max(0, u.limit - u.used);
    usage = (
      <>
        <h2>This month</h2>
        <p className="big-num">{u.used}<small> of {u.limit}</small></p>
        <Meter value={u.used / u.limit} large />
        <p className="t-meta mt-s">
          Bookings in {monthName(t)} on the Free plan. {u.reached ? "Customers can't book more times this month." : left + " left."}
        </p>
        {left <= 3 && <Link className="btn accent small mt-s" href="/owner/plan">Upgrade to Pro for unlimited bookings</Link>}
      </>
    );
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>{data.shop_name}</h1>
          <p className="t-meta">
            <span className={"chip" + (isPro ? " ok" : "")}>{data.plan.plan_name} plan</span>{" "}
            <Link href={`/shops/${data.shop_id}`}>See your public page</Link>
          </p>
        </div>
      </div>
      <div className="grid-2">
        <section>
          <h2>{data.date === t ? "Today's queue" : "Queue for " + fmtDateLong(data.date)}</h2>
          <div className="days-scroll">
            <div className="days" role="group" aria-label="Choose a day">
              {data.days.map((d, i) => {
                const pd = parseDate(d.date);
                return (
                  <button key={d.date} className="day" aria-pressed={d.date === data.date} onClick={() => setDay(d.date)}>
                    <span className="d-name">{i === 0 ? "Today" : DOW_S[pd.getDay()] + " " + pd.getDate()}</span>
                    {d.capacity == null ? (
                      <span className="d-count closed">Closed</span>
                    ) : (
                      <>
                        <span className="d-count">{d.count}<small> / {d.capacity}</small></span>
                        <Meter value={d.count / d.capacity} />
                      </>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
          <p className="fine">Each day shows bookings against a rough estimate of how many customers you can serve.</p>
          <div className="tickets mt">
            {data.queue.length ? (
              data.queue.map((b) => (
                <Ticket key={b.booking_id} b={b} owner href={`/bookings/${b.booking_id}`}
                  actions={<OwnerActions b={b} onDone={reload} />} />
              ))
            ) : (
              <p className="empty">No bookings {data.date === t ? "today" : "on this day"} yet.</p>
            )}
          </div>
        </section>
        <aside>
          <div className="panel">{usage}</div>
          <div className="panel mt">
            <h2>Latest alerts</h2>
            {data.alerts.length
              ? data.alerts.map((n) => <MsgLine key={n.notification_id} n={n} when={fmtDT(n.sent_at)} />)
              : <p className="t-meta">New bookings and cancellations show up here.</p>}
            <p className="fine">
              {data.pending_reminders}{data.pending_reminders === 1 ? " reminder" : " reminders"} scheduled for you and your
              customers. <Link href="/inbox">All messages</Link>
            </p>
          </div>
        </aside>
      </div>
    </>
  );
}

export default function OwnerDashboard() {
  return (
    <RequireRole role="shop_owner" message="Log in to manage your shop.">
      <Dashboard />
    </RequireRole>
  );
}
