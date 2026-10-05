// Dates, times and money, formatted exactly like the prototype (fmtDate, fmtDateLong, fmtDT, baht).
// Dates travel as "YYYY-MM-DD" strings and are read as calendar days, so time zones can't shift them.

export const DOW = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
export const DOW_S = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export const WEEK = [1, 2, 3, 4, 5, 6, 0]; // Monday first, as shown on shop pages and settings
export const MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
export const MON_S = MON.map((m) => m.slice(0, 3));
export const CATEGORIES = ["Hair salon", "Beauty and nails", "Massage and spa", "Car care", "Clinic", "Pet grooming", "Other"];
export const DURATIONS = [15, 30, 45, 60, 75, 90, 120, 150, 180, 240];
export const DEMO_PASSWORD = "demo1234";

export const pad = (n) => String(n).padStart(2, "0");

export function parseDate(s) {
  const p = String(s).split("-").map(Number);
  return new Date(p[0], (p[1] || 1) - 1, p[2] || 1);
}

export const isoDate = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());

export function addDays(s, n) {
  const d = parseDate(s);
  d.setDate(d.getDate() + n);
  return isoDate(d);
}

// Today in Bangkok as "YYYY-MM-DD", whatever time zone the viewer's computer uses
export function todayStr() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Bangkok" }).format(new Date());
}

export function fmtDate(s) {
  const d = parseDate(s);
  return DOW_S[d.getDay()] + " " + d.getDate() + " " + MON_S[d.getMonth()];
}

export function fmtDateLong(s) {
  const d = parseDate(s);
  return DOW[d.getDay()] + " " + d.getDate() + " " + MON[d.getMonth()];
}

export const monthName = (s) => MON[parseDate(s).getMonth()];

// A moment in time (ISO timestamp) shown in Bangkok time: "24 Sep, 11:00"
export function fmtDT(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Bangkok", day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(d).map((p) => [p.type, p.value])
  );
  return Number(parts.day) + " " + MON_S[Number(parts.month) - 1] + ", " + parts.hour + ":" + parts.minute;
}

export const baht = (n) => "฿" + Number(n || 0).toLocaleString("en-US");

// "Mon–Sat", "Tue, Thu" ... like the prototype's compressDays
export function compressDays(dows) {
  const idx = WEEK.map((d, i) => (dows.includes(d) ? i : -1)).filter((i) => i >= 0);
  const runs = [];
  let run = [];
  idx.forEach((i) => {
    if (run.length && i === run[run.length - 1] + 1) run.push(i);
    else {
      if (run.length) runs.push(run);
      run = [i];
    }
  });
  if (run.length) runs.push(run);
  return runs
    .map((r) => (r.length >= 3 ? DOW_S[WEEK[r[0]]] + "–" + DOW_S[WEEK[r[r.length - 1]]] : r.map((i) => DOW_S[WEEK[i]]).join(", ")))
    .join(", ");
}

// "Open Mon–Sat, 10:00–19:00." from a shop's opening-hours rows
export function openDaysText(hours) {
  if (!hours || !hours.length) return "Not taking bookings yet.";
  const same = hours.every((h) => h.open_time === hours[0].open_time && h.close_time === hours[0].close_time);
  const days = hours.length === 7 ? "daily" : compressDays(hours.map((h) => Number(h.day_of_week)));
  return "Open " + days + (same ? ", " + hours[0].open_time + "–" + hours[0].close_time : "") + ".";
}

// Booking status -> [label, chip colour], as in the prototype's STATUS
export const STATUS = {
  pending_payment: ["Awaiting deposit", "warn"],
  confirmed: ["Confirmed", "ok"],
  completed: ["Completed", "done"],
  cancelled: ["Cancelled", "bad"],
  no_show: ["No-show", "bad"],
  expired: ["Expired", "mute"],
};
export const METHOD = { promptpay: "PromptPay", cash: "cash", card: "card" };
export const chName = (c) => (c === "line" ? "LINE" : "Email");

// Milliseconds from now until an ISO timestamp (negative when it's in the past)
export const msUntil = (iso) => Date.parse(iso) - Date.now();
