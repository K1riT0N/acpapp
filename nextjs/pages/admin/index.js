import { useState } from "react";

import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import { useApi, usePoll } from "@/lib/api";
import { baht } from "@/lib/format";

const CHARTS = [
  { key: "users", label: "New users", format: (value) => value.toLocaleString() },
  { key: "bookings", label: "Bookings", format: (value) => value.toLocaleString() },
  { key: "transactions", label: "Transactions", format: (value) => value.toLocaleString() },
  { key: "transaction_volume", label: "Payment volume", format: baht },
];

function AnalyticsDashboard() {
  const [chartKey, setChartKey] = useState("bookings");
  const [selectedMonth, setSelectedMonth] = useState(null);
  const { data, error, reload } = useApi("/admin/dashboard", { keepPrevious: true });
  usePoll(reload);

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!data) return <Loading />;

  const chart = CHARTS.find((item) => item.key === chartKey) || CHARTS[0];
  const values = data.months.map((month) => month[chart.key]);
  const max = Math.max(...values, 1);
  const activeMonth = data.months.find((month) => month.month === selectedMonth) || data.months[data.months.length - 1];

  return (
    <>
      <div className="page-head admin-head">
        <div>
          <span className="chip ok">Admin</span>
          <h1>Business analytics</h1>
          <p className="lede">A platform-wide view of users, bookings, payments and subscription revenue.</p>
        </div>
        <p className="t-meta">Updated every 15 seconds</p>
      </div>

      <div className="admin-kpis">
        <section className="panel admin-kpi">
          <p className="t-meta">Active users</p>
          <p className="big-num">{data.active_users.toLocaleString()}</p>
          <p className="fine">Registered accounts. Account deactivation is not tracked.</p>
        </section>
        <section className="panel admin-kpi">
          <p className="t-meta">Businesses</p>
          <p className="big-num">{data.total_shops.toLocaleString()}</p>
          <p className="fine">Shops registered on the platform.</p>
        </section>
        <section className="panel admin-kpi">
          <p className="t-meta">Transactions this month</p>
          <p className="big-num">{data.transactions_this_month.toLocaleString()}</p>
          <p className="fine">{baht(data.transaction_volume_this_month)} in successful payments.</p>
        </section>
        <section className="panel admin-kpi">
          <p className="t-meta">Projected MRR</p>
          <p className="big-num">{baht(data.projected_mrr)}</p>
          <p className="fine">Monthly run-rate from currently active subscriptions.</p>
        </section>
        <section className="panel admin-kpi">
          <p className="t-meta">Projected ARR</p>
          <p className="big-num">{baht(data.projected_arr)}</p>
          <p className="fine">Projected MRR annualized (× 12).</p>
        </section>
      </div>

      <section className="panel admin-chart-panel">
        <div className="page-head">
          <div>
            <h2>Platform activity</h2>
            <p className="t-meta">Monthly totals for the last six months. Select a metric and month to inspect.</p>
          </div>
          <div className="row chart-controls" role="group" aria-label="Choose chart metric">
            {CHARTS.map((item) => (
              <button
                key={item.key}
                className={"btn small" + (item.key === chartKey ? " accent" : "")}
                aria-pressed={item.key === chartKey}
                onClick={() => setChartKey(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="admin-chart" role="group" aria-label={`${chart.label} by month`}>
          {data.months.map((month) => {
            const value = month[chart.key];
            const height = Math.max(value > 0 ? 5 : 1, (value / max) * 100);
            return (
              <button
                key={month.month}
                className="chart-month"
                aria-label={`${month.month}: ${chart.format(value)}`}
                aria-pressed={activeMonth?.month === month.month}
                onClick={() => setSelectedMonth(month.month)}
              >
                <span className="chart-value">{chart.format(value)}</span>
                <span className="chart-track">
                  <span className="chart-bar" style={{ height: `${height}%` }} />
                </span>
                <span className="chart-label">{month.month}</span>
              </button>
            );
          })}
        </div>
        {activeMonth && (
          <p className="fine chart-summary" aria-live="polite">
            {activeMonth.month}: {activeMonth.users.toLocaleString()} new users, {activeMonth.bookings.toLocaleString()} bookings,
            {" "}{activeMonth.transactions.toLocaleString()} successful transactions, and {baht(activeMonth.transaction_volume)} payment volume.
          </p>
        )}
      </section>
    </>
  );
}

export default function AdminDashboard() {
  return (
    <RequireRole role="admin" message="Log in with an Admin account to view platform analytics.">
      <AnalyticsDashboard />
    </RequireRole>
  );
}
