// The queue ticket (prototype: ticket()): marigold stub with time, date and reference, details on the right.
// b is a booking from the API; `owner` shows the customer instead of the shop.
import Link from "next/link";

import { baht, chName, fmtDate, STATUS } from "@/lib/format";

function moneyLine(b) {
  if (b.status === "pending_payment") return "Deposit " + baht(b.deposit_amount) + " due now, " + baht(b.remaining_amount) + " at the shop";
  if (b.status === "completed") return "Paid in full, " + baht(b.total_price);
  if (b.status === "cancelled" || b.status === "no_show") return "Deposit " + baht(b.deposit_amount) + " kept by the shop";
  if (b.status === "expired") return "No deposit paid";
  return "Deposit " + baht(b.deposit_amount) + " paid, " + baht(b.remaining_amount) + " at the shop";
}

export default function Ticket({ b, owner = false, href, actions }) {
  const [label, tone] = STATUS[b.status] || [b.status, "mute"];
  const isVoid = tone === "bad" || tone === "mute";
  const who = owner ? b.customer_name + (b.customer_phone ? ", " + b.customer_phone : "") : b.shop_name;
  return (
    <article className={"ticket" + (isVoid ? " is-void" : "")}>
      <div className="stub">
        <span className="stub-time">{b.start_time}</span>
        <span className="stub-date">{fmtDate(b.booking_date)}</span>
        <span className="stub-ref">{b.ref}</span>
      </div>
      <div className="t-body">
        <div className="t-head">
          <h3>{href ? <Link href={href}>{b.service_name}</Link> : b.service_name}</h3>
          <span className={"chip " + tone}>{label}</span>
        </div>
        <p className="t-meta">{who}</p>
        <p className="t-meta">{b.start_time}–{b.end_time}. {moneyLine(b)}.</p>
        {actions}
      </div>
    </article>
  );
}

// One message row with its LINE / Email label (prototype: msgLine)
export function MsgLine({ n, when }) {
  return (
    <div className="tl">
      <span className={"ch " + n.channel}>{chName(n.channel)}</span>
      <div>
        <p className="tl-title">{n.title}</p>
        <p className="t-meta">{when}</p>
      </div>
    </div>
  );
}
