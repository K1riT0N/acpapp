// Home: search and browse shops (prototype: vHome).
// The sample ticket on the right links straight to a free afternoon time in the coming week.
import Link from "next/link";
import { useEffect, useState } from "react";

import { Loading } from "@/components/States";
import { api, useApi } from "@/lib/api";
import { baht, fmtDate, fmtDateLong, openDaysText } from "@/lib/format";

function HeroTicket({ slot }) {
  const href = `/book/${slot.shop_id}/${slot.service_id}?date=${slot.date}&time=${slot.time}`;
  return (
    <Link className="hero-ticket" href={href}
      aria-label={`Book ${slot.service_name} at ${slot.shop_name} on ${fmtDateLong(slot.date)} at ${slot.time}`}>
      <article className="ticket">
        <div className="stub">
          <span className="stub-time">{slot.time}</span>
          <span className="stub-date">{fmtDate(slot.date)}</span>
          <span className="stub-ref">OPEN</span>
        </div>
        <div className="t-body">
          <h3>{slot.service_name}</h3>
          <p className="t-meta">{slot.shop_name}</p>
          <p className="t-meta">Hold it with a {baht(slot.deposit)} deposit. Reminder the day before.</p>
        </div>
      </article>
    </Link>
  );
}

function ShopRow({ shop }) {
  const svcs = shop.services;
  const min = svcs.length ? Math.min(...svcs.map((v) => v.price)) : null;
  return (
    <article className="shop-row">
      <div>
        <h3><Link href={`/shops/${shop.shop_id}`}>{shop.shop_name}</Link></h3>
        <p className="t-meta">{shop.category}, {shop.address}</p>
        <p className="t-meta">
          {svcs.length}{svcs.length === 1 ? " service" : " services"}
          {min != null ? ", from " + baht(min) : ""}. {openDaysText(shop.hours)}
        </p>
      </div>
      <Link className="btn" href={`/shops/${shop.shop_id}`}>View shop</Link>
    </article>
  );
}

export default function Home() {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const all = useApi("/shops"); // every shop, for the category pills and the "no shops yet" message
  const { data: sample } = useApi("/shops/sample-slot");
  const [shown, setShown] = useState(null);

  // Ask the API for matching shops, waiting 250 ms after the last key press
  useEffect(() => {
    if (!q.trim() && !cat) {
      setShown(null);
      return;
    }
    const params = new URLSearchParams({ q: q.trim(), category: cat });
    let stale = false;
    const t = setTimeout(() => {
      api(`/shops?${params}`).then((d) => !stale && setShown(d)).catch(() => {});
    }, 250);
    return () => {
      stale = true;
      clearTimeout(t);
    };
  }, [q, cat]);

  if (all.error) return <div className="empty-state"><h1>We couldn&apos;t load the shops.</h1><p className="lede">{all.error.message}</p></div>;
  if (!all.data) return <Loading text="Loading shops…" />;

  const shops = all.data;
  const list = shown || shops;
  const cats = [...new Set(shops.map((s) => s.category).filter(Boolean))].sort();

  let listHtml;
  if (!shops.length) {
    listHtml = <p className="empty">No shops are listed yet. <Link href="/signup">Sign up as a shop owner</Link> to add the first one.</p>;
  } else if (!list.length) {
    listHtml = <p className="empty">No shops match that search. Try a service like &quot;massage&quot;, or pick All shops.</p>;
  } else {
    listHtml = list.map((s) => <ShopRow key={s.shop_id} shop={s} />);
  }

  return (
    <>
      <section className="hero">
        <div>
          <h1>Find a local shop and book your time.</h1>
          <p className="lede">
            Pick a service and a time, then pay a small deposit to hold it. You&apos;ll get a reminder on LINE before you go.
          </p>
          <div className="search">
            <label className="sr" htmlFor="q">Search shops</label>
            <input id="q" type="search" placeholder="Search by shop, service or area" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          {cats.length > 0 && (
            <div className="pills" role="group" aria-label="Filter by category">
              {["", ...cats].map((c) => (
                <button key={c || "all"} className="pill" aria-pressed={cat === c} onClick={() => setCat(c)}>
                  {c || "All shops"}
                </button>
              ))}
            </div>
          )}
        </div>
        {sample && <HeroTicket slot={sample} />}
      </section>

      <section aria-labelledby="shops-h">
        <h2 id="shops-h">
          {list.length ? list.length + (list.length === 1 ? " shop" : " shops") + " taking bookings" : "Shops"}
        </h2>
        {listHtml}
      </section>
    </>
  );
}
