// Every booking for the owner's shop, with filters (prototype: vOwnerBookings). Refreshes every 15 seconds.
import { useState } from "react";

import BookingTable from "@/components/BookingTable";
import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import { usePoll, useApi } from "@/lib/api";

const FILTERS = [
  ["upcoming", "Upcoming"],
  ["pending", "Awaiting deposit"],
  ["completed", "Completed"],
  ["cancelled", "Cancelled"],
  ["no_show", "No-show"],
  ["all", "All"],
];

function OwnerBookings() {
  const [filter, setFilter] = useState("upcoming");
  const { data, error, reload } = useApi(`/owner/bookings?filter=${filter}`, { keepPrevious: true });
  usePoll(reload);

  if (error) return <p className="err" role="alert">{error.message}</p>;
  if (!data) return <Loading />;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Bookings</h1>
          <p className="lede">Every booking for {data.shop_name}, with the deposit and what&apos;s left to pay at the shop.</p>
        </div>
      </div>
      <div className="pills" role="group" aria-label="Filter bookings">
        {FILTERS.map(([key, label]) => (
          <button key={key} className="pill" aria-pressed={key === filter} onClick={() => setFilter(key)}>
            {label} <span className="count">{data.counts[key]}</span>
          </button>
        ))}
      </div>
      <div className="mt">
        {data.filter === filter && data.rows.length ? (
          <BookingTable rows={data.rows} owner />
        ) : data.filter === filter ? (
          <p className="empty">No bookings here yet.</p>
        ) : (
          <Loading />
        )}
      </div>
    </>
  );
}

export default function OwnerBookingsPage() {
  return (
    <RequireRole role="shop_owner" message="Log in to manage your shop.">
      <OwnerBookings />
    </RequireRole>
  );
}
