// The customer's bookings (prototype: vMy): tickets for what's coming up, a table for the rest.
import Link from "next/link";

import BookingTable from "@/components/BookingTable";
import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import Ticket from "@/components/Ticket";
import { useApi } from "@/lib/api";
import { todayStr } from "@/lib/format";

const key = (b) => b.booking_date + " " + b.start_time;

function MyBookings() {
  const { data, error } = useApi("/bookings/me");
  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!data) return <Loading />;

  const t = todayStr();
  const up = data
    .filter((b) => b.booking_date >= t && (b.status === "confirmed" || b.hold_active))
    .sort((a, b) => key(a).localeCompare(key(b)));
  const past = data.filter((b) => !up.includes(b)).sort((a, b) => key(b).localeCompare(key(a)));

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My bookings</h1>
          <p className="lede">Show the reference code on your ticket when you arrive.</p>
        </div>
        <Link className="btn" href="/">Book something new</Link>
      </div>
      <section>
        <h2>Coming up</h2>
        {up.length ? (
          <div className="tickets">
            {up.map((b) => (
              <Ticket key={b.booking_id} b={b}
                href={b.status === "pending_payment" ? `/pay/${b.booking_id}` : `/bookings/${b.booking_id}`} />
            ))}
          </div>
        ) : (
          <div className="empty-state small">
            <p className="empty">No upcoming bookings.</p>
            <Link className="btn primary" href="/">Find a shop</Link>
          </div>
        )}
      </section>
      <section>
        <h2>History</h2>
        {past.length ? <BookingTable rows={past} /> : <p className="empty">Past bookings will show up here.</p>}
      </section>
    </>
  );
}

export default function MyPage() {
  return (
    <RequireRole role="customer" message="Log in to see your bookings.">
      <MyBookings />
    </RequireRole>
  );
}
