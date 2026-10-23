// Pay the deposit to confirm (prototype: vPay): countdown, ticket, policy checkbox and the test QR code.
import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import FakeQR from "@/components/FakeQR";
import RequireRole from "@/components/RequireRole";
import { Loading, NotFound } from "@/components/States";
import Ticket from "@/components/Ticket";
import { useToast } from "@/components/Toasts";
import { api, useApi } from "@/lib/api";
import { useMessages } from "@/lib/messages";
import { baht, fmtDateLong, msUntil, pad } from "@/lib/format";

// "14:59" style countdown, updated every second
function useCountdown(iso) {
  const [left, setLeft] = useState(() => (iso ? msUntil(iso) : 0));
  useEffect(() => {
    if (!iso) return;
    setLeft(msUntil(iso));
    const t = setInterval(() => setLeft(msUntil(iso)), 1000);
    return () => clearInterval(t);
  }, [iso]);
  return left;
}

function Pay() {
  const router = useRouter();
  const id = router.query.bookingId;
  const toast = useToast();
  const { reload: reloadMessages } = useMessages();
  const { data, error } = useApi(id ? `/bookings/${encodeURIComponent(id)}` : null);
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const b = data?.booking;
  const left = useCountdown(b?.hold_expires_at);
  const notPending = b && b.status !== "pending_payment";

  // Already paid (or released): show the booking page instead
  useEffect(() => {
    if (notPending) router.replace(`/bookings/${b.booking_id}`);
  }, [notPending]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error || (data && data.viewer !== "customer")) return <NotFound message="We couldn't find that booking." />;
  if (!b || notPending) return <Loading />;

  if (!b.hold_active || left <= 0) {
    return (
      <div className="empty-state">
        <h1>Your hold on this time ran out.</h1>
        <p className="lede">Times are held for 15 minutes while you pay. Pick a time again to book.</p>
        <Link className="btn primary" href={`/shops/${b.shop_id}`}>Back to {b.shop_name}</Link>
      </div>
    );
  }

  async function pay() {
    setBusy(true);
    try {
      await api(`/bookings/${b.booking_id}/pay-deposit`, { method: "POST", body: { policy_accepted: true } });
      reloadMessages();
      router.push(`/bookings/${b.booking_id}?confirmed=1`);
    } catch (e) {
      toast(e.message);
      setBusy(false);
    }
  }

  async function release() {
    setBusy(true);
    try {
      await api(`/bookings/${b.booking_id}/release`, { method: "POST" });
      toast("Time released.");
      router.push(`/shops/${b.shop_id}`);
    } catch (e) {
      toast(e.message);
      setBusy(false);
    }
  }

  return (
    <>
      <p className="crumb"><Link href={`/shops/${b.shop_id}`}>{b.shop_name}</Link></p>
      <h1>Pay the deposit to confirm</h1>
      <p className="lede">
        We&apos;re holding {b.start_time} on {fmtDateLong(b.booking_date)} for you for another{" "}
        <strong id="hold-left">{Math.floor(left / 60000)}:{pad(Math.floor((left % 60000) / 1000))}</strong>.
      </p>
      <div className="grid-2 mt">
        <div>
          <Ticket b={b} />
          <div className="panel mt">
            <dl className="kv">
              <dt>Service price</dt><dd>{baht(b.total_price)}</dd>
              <dt className="strong">Deposit now</dt><dd className="strong">{baht(b.deposit_amount)}</dd>
              <dt>Pay at the shop</dt><dd>{baht(b.remaining_amount)}</dd>
            </dl>
            <label className="check">
              <input type="checkbox" id="agree" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
              <span>I understand the {baht(b.deposit_amount)} deposit is not refunded if I cancel or don&apos;t show up.</span>
            </label>
          </div>
        </div>
        <div className="panel pay">
          <h2>Scan with any Thai banking app</h2>
          <FakeQR seed={b.booking_id} />
          <p className="amount">{baht(b.deposit_amount)}</p>
          <button className="btn primary wide" onClick={pay} disabled={!agree || busy}>Simulate successful payment</button>
          {!agree && <p className="fine">Tick the deposit policy first.</p>}
          <p className="fine">
            PromptPay test mode, so no real money moves. In the finished system the payment gateway tells our server when the
            payment arrives.
          </p>
          <button className="btn link mt-s" onClick={release} disabled={busy}>Cancel and release this time</button>
        </div>
      </div>
    </>
  );
}

export default function PayPage() {
  return (
    <RequireRole role="customer" message="Log in to pay your deposit.">
      <Pay />
    </RequireRole>
  );
}
