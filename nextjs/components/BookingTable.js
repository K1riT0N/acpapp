// Table of bookings (prototype: bookingTable). `owner` shows the customer column instead of the shop.
import Link from "next/link";

import { baht, fmtDate, STATUS } from "@/lib/format";

export default function BookingTable({ rows, owner = false }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Time</th><th>{owner ? "Customer" : "Shop"}</th><th>Service</th><th>Status</th>
            <th className="num">Deposit</th><th className="num">At shop</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((b) => {
            const [label, tone] = STATUS[b.status] || [b.status, "mute"];
            return (
              <tr key={b.booking_id}>
                <td><Link href={`/bookings/${b.booking_id}`}>{fmtDate(b.booking_date)}</Link></td>
                <td>{b.start_time}</td>
                <td>{owner ? b.customer_name : b.shop_name}</td>
                <td>{b.service_name}</td>
                <td><span className={"chip " + tone}>{label}</span></td>
                <td className="num">{baht(b.deposit_amount)}</td>
                <td className="num">{baht(b.remaining_amount)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
