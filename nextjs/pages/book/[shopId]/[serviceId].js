// Choose a service, a day and a time, then hold it (prototype: vBook).
// The chosen day and time are kept in the URL (?date=...&time=...), so "Log in to book" can bring the
// customer back to exactly the same choice after logging in.
import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useRef, useState } from "react";

import { Loading, NotFound } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { loginHref, useAuth } from "@/lib/auth";
import { baht, DOW, DOW_S, fmtDate, fmtDateLong, MON_S, monthName, parseDate, todayStr } from "@/lib/format";

export default function Book() {
  const router = useRouter();
  const { shopId, serviceId } = router.query;
  const { user } = useAuth();
  const toast = useToast();
  const { data: shop, error } = useApi(shopId ? `/shops/${encodeURIComponent(shopId)}` : null);

  const [svcId, setSvcId] = useState(null); // chosen service; starts from the URL
  const [cal, setCal] = useState(null);
  const [date, setDate] = useState(null);
  const [time, setTime] = useState(null);
  const [slotData, setSlotData] = useState(null);
  const [busy, setBusy] = useState(false);
  const fromUrl = useRef(null); // ?date and ?time when the page opened, used once

  const svcs = shop?.services || [];
  const svc = svcs.find((v) => v.service_id === (svcId || serviceId)) || svcs[0];
  const svcKey = svc?.service_id;

  if (router.isReady && fromUrl.current === null) {
    fromUrl.current = { date: router.query.date, time: router.query.time };
  }

  // Days: which are open, and the default day (the first with a free time)
  useEffect(() => {
    if (!shop || !svcKey) return;
    let stale = false;
    api(`/shops/${shop.shop_id}/calendar?service_id=${svcKey}`).then((c) => {
      if (stale) return;
      setCal(c);
      setDate((d) => {
        if (d && c.some((x) => x.date === d)) return d;
        const wanted = fromUrl.current?.date;
        if (wanted && c.some((x) => x.date === wanted && x.open)) return wanted;
        return (c.find((x) => x.has_free_slot) || c[0]).date;
      });
    });
    return () => { stale = true; };
  }, [shop, svcKey]);

  // Times for the chosen day, plus the shop's monthly limit
  const loadSlots = useCallback(() => {
    if (!shop || !svcKey || !date) return Promise.resolve();
    return api(`/shops/${shop.shop_id}/slots?service_id=${svcKey}&date=${date}`).then((d) => {
      setSlotData({ ...d, date, svcKey });
      setTime((t) => {
        const want = t || fromUrl.current?.time;
        if (fromUrl.current) fromUrl.current.time = null;
        return want && d.slots.some((x) => x.time === want && !x.full && !x.past) ? want : null;
      });
    });
  }, [shop, svcKey, date]);

  useEffect(() => { loadSlots(); }, [loadSlots]);

  // Keep the URL in step with the choice (without reloading the page)
  useEffect(() => {
    if (!shop || !svcKey || !date) return;
    const query = { shopId: shop.shop_id, serviceId: svcKey, date, ...(time ? { time } : {}) };
    if (router.query.date !== date || router.query.time !== query.time || router.query.serviceId !== svcKey) {
      router.replace({ pathname: router.pathname, query }, undefined, { shallow: true, scroll: false });
    }
  }, [shop, svcKey, date, time]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <NotFound message={error.status === 404 ? error.message : "We couldn't load that shop."} />;
  if (!shop) return <Loading />;
  if (!svcs.length) return <NotFound message={shop.shop_name + " isn't taking bookings yet."} />;

  const today = todayStr();
  const dur = svc.duration_min;
  const dep = Math.round((svc.price * shop.deposit_percent) / 100);
  const ready = slotData && slotData.date === date && slotData.svcKey === svcKey;

  // The URL follows the page's state (see the effect above), never the other way round
  function pickService(id) {
    setSvcId(id);
    setTime(null);
  }

  async function startBooking() {
    if (!user) {
      router.push(loginHref(router.asPath));
      return;
    }
    setBusy(true);
    try {
      const b = await api("/bookings", {
        method: "POST",
        body: { shop_id: shop.shop_id, service_id: svcKey, booking_date: date, start_time: time },
      });
      router.push(`/pay/${b.booking_id}`);
    } catch (e) {
      toast(e.message);
      setTime(null);
      await loadSlots();
      setBusy(false);
    }
  }

  // ----- the three steps -----
  const dateButtons = (cal || []).map((c) => {
    const pd = parseDate(c.date);
    return (
      <button key={c.date} className="date" aria-pressed={c.date === date} disabled={!c.open}
        aria-label={fmtDateLong(c.date) + (c.open ? "" : ", closed")}
        onClick={() => { setDate(c.date); setTime(null); }}>
        <span className="dn">{c.date === today ? "Today" : DOW_S[pd.getDay()]}</span>
        <span className="dd">{pd.getDate()}</span>
        <span className="dm">{c.open ? MON_S[pd.getMonth()] : "Closed"}</span>
      </button>
    );
  });

  let slotHtml = <Loading />;
  if (ready) {
    const upcoming = slotData.slots.filter((x) => !x.past);
    const avail = upcoming.filter((x) => !x.full);
    if (slotData.closed) slotHtml = <p className="empty">Closed on {DOW[parseDate(date).getDay()]}s. Pick another day.</p>;
    else if (!avail.length) slotHtml = <p className="empty">No times left on this day. Pick another day.</p>;
    else {
      slotHtml = (
        <div className="slots" role="group" aria-label="Available times">
          {upcoming.map((x) => (
            <button key={x.time} className="slot" aria-pressed={x.time === time} disabled={x.full} onClick={() => setTime(x.time)}>
              {x.time}
              {x.full ? <small>Full</small> : x.cap > 1 ? <small>{x.cap - x.used} left</small> : null}
            </button>
          ))}
        </div>
      );
    }
  }

  let cta;
  if (ready && slotData.limit.reached) {
    cta = (
      <div className="warnbox">
        {shop.shop_name} has reached its booking limit for {monthName(date)}. Try a date next month, or call the shop on {shop.phone}.
      </div>
    );
  } else if (user && user.role !== "customer") {
    cta = <p className="note">You&apos;re logged in as a shop owner. Log in with a customer account to book.</p>;
  } else {
    cta = (
      <>
        <button className="btn primary wide" onClick={startBooking} disabled={!time || busy}>
          {user ? "Continue to deposit" : "Log in to book"}
        </button>
        {!time && <p className="fine">Pick a time to continue.</p>}
      </>
    );
  }

  return (
    <>
      <p className="crumb"><Link href={`/shops/${shop.shop_id}`}>{shop.shop_name}</Link></p>
      <h1>Book at {shop.shop_name}</h1>
      <div className="grid-2 mt">
        <div>
          <div className="step">
            <h2>Choose a service</h2>
            <div className="opt-list">
              {svcs.map((v) => (
                <button key={v.service_id} className="opt" aria-pressed={v.service_id === svcKey} onClick={() => pickService(v.service_id)}>
                  <span>
                    <strong>{v.service_name}</strong>
                    <span className="t-meta block">{v.duration_min} min</span>
                  </span>
                  <span className="price">{baht(v.price)}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="step">
            <h2>Choose a day</h2>
            <div className="dates">{cal ? dateButtons : <Loading />}</div>
          </div>
          <div className="step">
            <h2>Choose a time</h2>
            {slotHtml}
          </div>
        </div>
        <aside className="panel summary">
          <h2>Your booking</h2>
          <dl className="kv">
            <dt>Service</dt><dd>{svc.service_name}</dd>
            <dt>Length</dt><dd>{dur} min</dd>
            <dt>When</dt><dd>{time ? fmtDate(date) + ", " + time : "Not picked yet"}</dd>
          </dl>
          <div className="divider"></div>
          <dl className="kv">
            <dt>Service price</dt><dd>{baht(svc.price)}</dd>
            <dt className="strong">Deposit now ({shop.deposit_percent}%)</dt><dd className="strong">{baht(dep)}</dd>
            <dt>Pay at the shop</dt><dd>{baht(svc.price - dep)}</dd>
          </dl>
          {cta}
          <p className="fine">The deposit isn&apos;t refunded if you cancel or don&apos;t show up.</p>
        </aside>
      </div>
    </>
  );
}
