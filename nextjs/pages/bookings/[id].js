// One booking, for its customer or the shop's owner (prototype: vBooking).
// The customer can cancel a confirmed booking before it starts; the owner can mark it completed or a no-show.
import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";

import OwnerActions from "@/components/OwnerActions";
import RequireRole from "@/components/RequireRole";
import { Loading, NotFound } from "@/components/States";
import Ticket, { MsgLine } from "@/components/Ticket";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { baht, fmtDateLong, fmtDT, METHOD, startsInFuture } from "@/lib/format";
import { useMessages } from "@/lib/messages";

function messageWhen(n) {
  if (n.status === "sent") return "Sent " + fmtDT(n.sent_at);
  if (n.status === "pending") return "Scheduled for " + fmtDT(n.scheduled_at);
  return "Not sent because the booking changed";
}

function BookingView() {
  const router = useRouter();
  const id = router.query.id;
  const toast = useToast();
  const { reload: reloadMessages } = useMessages();
  const { data, error, setData } = useApi(id ? `/bookings/${encodeURIComponent(id)}` : null);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [busy, setBusy] = useState(false);

  if (error) return <NotFound message={error.status === 404 ? error.message : "We couldn't find that booking."} />;
  if (!data) return <Loading />;

  const { booking: b, shop, viewer, payments, notifications } = data;
  const isOwner = viewer === "owner";

  // After a change, read the booking again (status, payments and messages all change)
  const refresh = () => api(`/bookings/${b.booking_id}`).then(setData).then(reloadMessages).catch(() => {});

  async function cancel() {
    setBusy(true);
    try {
      setData(await api(`/bookings/${b.booking_id}/cancel`, { method: "POST" }));
      setConfirmCancel(false);
      toast("Booking cancelled.");
      reloadMessages();
    } catch (e) {
      toast(e.message);
    }
    setBusy(false);
  }

  let actions = null;
  if (isOwner) {
    actions = <OwnerActions b={b} onDone={refresh} />;
  } else if (b.status === "pending_payment" && b.hold_active) {
    actions = (
      <div className="t-actions">
        <Link className="btn primary small" href={`/pay/${b.booking_id}`}>Pay deposit</Link>
      </div>
    );
  } else if (b.status === "confirmed" && startsInFuture(b)) {
    actions = confirmCancel ? (
      <div className="warnbox mt-s">
        <p>Cancel this booking? The {baht(b.deposit_amount)} deposit won&apos;t be refunded.</p>
        <div className="row">
          <button className="btn danger small" disabled={busy} onClick={cancel}>Cancel booking</button>
          <button className="btn small" onClick={() => setConfirmCancel(false)}>Keep booking</button>
        </div>
      </div>
    ) : (
      <div className="t-actions">
        <button className="btn danger small" onClick={() => setConfirmCancel(true)}>Cancel booking</button>
      </div>
    );
  }

  return (
    <>
      <p className="crumb">
        <Link href={isOwner ? "/owner/bookings" : "/my"}>{isOwner ? "All bookings" : "My bookings"}</Link>
      </p>
      {!isOwner && router.query.confirmed && b.status === "confirmed" && (
        <div className="okbox" role="status">
          Booking confirmed. {shop.shop_name} has been told you&apos;re coming, and you&apos;ll get a reminder before your appointment.
        </div>
      )}
      <h1>{b.service_name}</h1>
      <p className="lede">
        {isOwner ? b.customer_name : shop.shop_name}, {fmtDateLong(b.booking_date)} at {b.start_time}.
      </p>
      <div className="grid-2 mt">
        <div>
          <Ticket b={b} owner={isOwner} actions={actions} />
          <section className="mt">
            <h2>Messages about this booking</h2>
            {notifications.length
              ? notifications.map((n) => <MsgLine key={n.notification_id} n={n} when={messageWhen(n)} />)
              : <p className="empty">No messages yet.</p>}
          </section>
        </div>
        <aside className="panel">
          <h2>Payment</h2>
          <dl className="kv">
            <dt>Service price</dt><dd>{baht(b.total_price)}</dd>
            <dt>Deposit ({b.total_price ? Math.round((b.deposit_amount / b.total_price) * 100) : 0}%)</dt><dd>{baht(b.deposit_amount)}</dd>
            <dt>Pay at the shop</dt><dd>{baht(b.remaining_amount)}</dd>
          </dl>
          <div className="divider"></div>
          <h3>Payments recorded</h3>
          {payments.length ? (
            payments.map((p) => (
              <div key={p.payment_id}>
                <div className="pay-row">
                  <span>{p.payment_type === "deposit" ? "Deposit" : "Rest of the price"}, {METHOD[p.method] || p.method}</span>
                  <span>{baht(p.amount)}</span>
                </div>
                <p className="fine tight">{fmtDT(p.paid_at)}{p.gateway_ref ? ", ref " + p.gateway_ref : ""}</p>
              </div>
            ))
          ) : (
            <p className="t-meta">Nothing paid yet.</p>
          )}
          {(b.status === "cancelled" || b.status === "no_show") && (
            <p className="note mt">The deposit isn&apos;t refunded for cancellations and no-shows.</p>
          )}
        </aside>
      </div>
    </>
  );
}

export default function BookingPage() {
  return (
    <RequireRole role={null} message="Log in to see this booking.">
      <BookingView />
    </RequireRole>
  );
}
