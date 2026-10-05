// One booking, for its customer or the shop's owner (prototype: vBooking).
// Step 9 adds the customer's Cancel button and the owner's Mark completed / No-show buttons.
import Link from "next/link";
import { useRouter } from "next/router";

import RequireRole from "@/components/RequireRole";
import { Loading, NotFound } from "@/components/States";
import Ticket, { MsgLine } from "@/components/Ticket";
import { useApi } from "@/lib/api";
import { baht, fmtDateLong, fmtDT, METHOD } from "@/lib/format";

function messageWhen(n) {
  if (n.status === "sent") return "Sent " + fmtDT(n.sent_at);
  if (n.status === "pending") return "Scheduled for " + fmtDT(n.scheduled_at);
  return "Not sent because the booking changed";
}

function BookingView() {
  const router = useRouter();
  const id = router.query.id;
  const { data, error } = useApi(id ? `/bookings/${encodeURIComponent(id)}` : null);

  if (error) return <NotFound message={error.status === 404 ? error.message : "We couldn't find that booking."} />;
  if (!data) return <Loading />;

  const { booking: b, shop, viewer, payments, notifications } = data;
  const isOwner = viewer === "owner";

  let actions = null;
  if (!isOwner && b.status === "pending_payment" && b.hold_active) {
    actions = (
      <div className="t-actions">
        <Link className="btn primary small" href={`/pay/${b.booking_id}`}>Pay deposit</Link>
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
