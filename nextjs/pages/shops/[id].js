// One shop's public page (prototype: vShop): services with Book buttons, opening hours and the deposit rule.
import Link from "next/link";
import { useRouter } from "next/router";

import { Loading, NotFound } from "@/components/States";
import { useApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { baht, DOW, parseDate, todayStr, WEEK } from "@/lib/format";

export default function ShopPage() {
  const router = useRouter();
  const id = router.query.id;
  const { user } = useAuth();
  const { data: s, error } = useApi(id ? `/shops/${encodeURIComponent(id)}` : null);

  if (error) return <NotFound message={error.status === 404 ? error.message : "We couldn't load that shop."} />;
  if (!s) return <Loading />;

  const mine = user && user.user_id === s.owner_id;
  const todayDow = parseDate(todayStr()).getDay();
  const hoursByDay = Object.fromEntries(s.hours.map((h) => [h.day_of_week, h]));

  return (
    <>
      <p className="crumb"><Link href="/">All shops</Link></p>
      <div className="grid-2">
        <div>
          <h1>{s.shop_name}</h1>
          <p className="t-meta">{s.category}. {s.address}. {s.phone}</p>
          {s.description && <p className="lede mt-s">{s.description}</p>}
          {mine && <p><Link className="btn small" href="/owner/settings">Edit shop details</Link></p>}
          <h2 className="mt">Services</h2>
          {s.services.length ? (
            <div>
              {s.services.map((v) => (
                <div className="svc-row" key={v.service_id}>
                  <div>
                    <h3>{v.service_name}</h3>
                    <p className="t-meta">{v.duration_min} min</p>
                  </div>
                  <span className="price">{baht(v.price)}</span>
                  <Link className="btn accent small" href={`/book/${s.shop_id}/${v.service_id}`}>Book</Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty">This shop hasn&apos;t added services yet.</p>
          )}
        </div>
        <aside className="panel">
          <h2>Opening hours</h2>
          <table className="hours">
            <tbody>
              {WEEK.map((d) => {
                const h = hoursByDay[d];
                return (
                  <tr key={d} className={d === todayDow ? "today" : undefined}>
                    <td>{DOW[d]}{d === todayDow ? " (today)" : ""}</td>
                    <td>{h ? h.open_time + "–" + h.close_time : "Closed"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="divider"></div>
          <p className="t-meta">
            A {s.deposit_percent}% deposit holds your booking, and you pay the rest at the shop. The deposit isn&apos;t refunded if
            you cancel or don&apos;t show up.
          </p>
        </aside>
      </div>
    </>
  );
}
