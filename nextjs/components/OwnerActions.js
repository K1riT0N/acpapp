// The owner's buttons on a confirmed booking (prototype: ownerActions):
// on the day, "Mark completed" (then choose how the rest was paid) or "No-show" (then confirm).
// Inline confirm steps instead of browser pop-ups.
import { useState } from "react";

import { useToast } from "@/components/Toasts";
import { api } from "@/lib/api";
import { baht, todayStr } from "@/lib/format";

export default function OwnerActions({ b, onDone }) {
  const toast = useToast();
  const [mode, setMode] = useState(null); // null | "complete" | "noshow"
  const [busy, setBusy] = useState(false);

  if (b.status !== "confirmed") return null;
  if (b.booking_date > todayStr()) return <p className="fine">You can mark this completed or a no-show on the day.</p>;

  async function run(path, body, message) {
    setBusy(true);
    try {
      await api(`/owner/bookings/${b.booking_id}/${path}`, { method: "POST", body });
      toast(message);
      setMode(null);
      onDone && onDone();
    } catch (e) {
      toast(e.message);
    }
    setBusy(false);
  }

  if (mode === "complete") {
    const done = "Marked completed. " + baht(b.remaining_amount) + " recorded.";
    return (
      <div className="t-actions">
        <span className="t-meta">{baht(b.remaining_amount)} paid by</span>
        <button className="btn small" disabled={busy} onClick={() => run("complete", { method: "cash" }, done)}>Cash</button>
        <button className="btn small" disabled={busy} onClick={() => run("complete", { method: "promptpay" }, done)}>PromptPay</button>
        <button className="btn small" disabled={busy} onClick={() => run("complete", { method: "card" }, done)}>Card</button>
        <button className="btn link small" onClick={() => setMode(null)}>Back</button>
      </div>
    );
  }
  if (mode === "noshow") {
    return (
      <div className="t-actions">
        <span className="t-meta">Mark as a no-show? The deposit is kept.</span>
        <button className="btn danger small" disabled={busy} onClick={() => run("no-show", undefined, "Marked as a no-show.")}>
          Mark no-show
        </button>
        <button className="btn link small" onClick={() => setMode(null)}>Back</button>
      </div>
    );
  }
  return (
    <div className="t-actions">
      <button className="btn primary small" onClick={() => setMode("complete")}>Mark completed</button>
      <button className="btn small" onClick={() => setMode("noshow")}>No-show</button>
    </div>
  );
}
