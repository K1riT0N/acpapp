// Messages (prototype: vInbox): what was "sent" on LINE or email, and what's scheduled.
// Opening the page marks everything read, but messages that were new keep their dot until you leave.
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import RequireRole from "@/components/RequireRole";
import { Loading } from "@/components/States";
import { MsgLine } from "@/components/Ticket";
import { useToast } from "@/components/Toasts";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { chName, fmtDT } from "@/lib/format";
import { useMessages } from "@/lib/messages";

function Inbox() {
  const { user } = useAuth();
  const toast = useToast();
  const { inbox, reload } = useMessages();
  const [newIds, setNewIds] = useState(null);
  const opened = useRef(false);

  // When the page opens: fetch fresh messages, remember which were unread (they keep their dot while
  // you're here), then mark them all read on the server so the header badge clears.
  useEffect(() => {
    if (opened.current) return;
    opened.current = true;
    reload().then((data) => {
      if (!data) {
        setNewIds(new Set()); // couldn't load: show the page with what we have
        return;
      }
      setNewIds(new Set(data.sent.filter((n) => !n.read).map((n) => n.notification_id)));
      if (data.unread_count) api("/notifications/read-all", { method: "POST" }).then(reload).catch(() => {});
    });
  }, [reload]);

  if (!newIds) return <Loading />;
  if (!inbox) return <p className="empty">We couldn&apos;t load your messages. Try again in a moment.</p>;

  async function sendNow() {
    try {
      const { count } = await api("/notifications/send-now", { method: "POST" });
      toast("Sent " + count + (count === 1 ? " message." : " messages."));
      reload();
    } catch (e) {
      toast(e.message);
    }
  }

  const via = user.line_user_id ? "LINE" : "email";
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Messages</h1>
          <p className="lede">Alerts and reminders for your {via}. This prototype shows them here instead of sending them.</p>
        </div>
      </div>
      <div className="grid-2">
        <section aria-label="Sent messages">
          {inbox.sent.length ? (
            inbox.sent.map((n) => (
              <article key={n.notification_id} className={"msg" + (newIds.has(n.notification_id) || !n.read ? " unread" : "")}>
                <span className={"ch " + n.channel}>{chName(n.channel)}</span>
                <div>
                  <h3>{n.title}</h3>
                  <p className="t-meta">{n.body}</p>
                  {n.booking_id && <Link className="small-link" href={`/bookings/${n.booking_id}`}>View booking</Link>}
                </div>
                <time className="t-meta" dateTime={n.sent_at}>{fmtDT(n.sent_at)}</time>
              </article>
            ))
          ) : (
            <p className="empty">No messages yet. You&apos;ll get one each time a booking is made, cancelled or coming up.</p>
          )}
        </section>
        <aside className="panel">
          <h2>Scheduled</h2>
          {inbox.scheduled.length ? (
            <>
              {inbox.scheduled.map((n) => <MsgLine key={n.notification_id} n={n} when={"Sends " + fmtDT(n.scheduled_at)} />)}
              <button className="btn small mt-s" onClick={sendNow}>Send these now</button>
              <p className="fine">Demo shortcut. Normally the reminder job sends each message at its scheduled time.</p>
            </>
          ) : (
            <p className="t-meta">No reminders waiting to go out.</p>
          )}
        </aside>
      </div>
    </>
  );
}

export default function InboxPage() {
  return (
    <RequireRole role={null} message="Log in to see your messages.">
      <Inbox />
    </RequireRole>
  );
}
