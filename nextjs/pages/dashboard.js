import { useState } from "react";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";

import { api } from "@/lib/api";

const queue = [
  { day: "Today", count: 2, limit: 14 },
  { day: "Thu 24", count: 0, limit: 14 },
  { day: "Fri 25", count: 1, limit: 14 },
  { day: "Sat 26", count: 0, limit: 14 },
  { day: "Sun 27", count: 0, limit: 14 },
  { day: "Mon 28", closed: true },
  { day: "Tue 29", count: 0, limit: 14 },
];

const alerts = [
  { title: "New booking: Hair colouring", date: "22 Sep, 19:43" },
  { title: "New booking: Hair spa treatment", date: "21 Sep, 11:18" },
  { title: "New booking: Haircut and blow-dry", date: "19 Sep, 14:03" },
];

export default function Dashboard() {
  const router = useRouter();
  const [bookingStates, setBookingStates] = useState({ first: "No-show", second: "Confirmed" });

  function updateBooking(id, status) {
    setBookingStates((current) => ({ ...current, [id]: status }));
  }

  async function handleLogout() {
    try {
      await api("/api/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
    }
  }

  return (
    <>
      <Head>
        <title>Dashboard | Nadd</title>
        <meta name="description" content="Manage your shop bookings on Nadd." />
      </Head>
      <main className="min-h-screen bg-[#0e1324] text-[#e8ecf8]">
        <header className="border-b border-[#26304b] bg-[#171e35]">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-5 py-3 sm:px-8">
            <div className="flex items-center gap-5">
              <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight" aria-label="Nadd home">
                Nadd <span className="rounded bg-[#f2b93f] px-1.5 py-0.5 text-xs font-bold text-[#201a0c]">นัด</span>
              </Link>
              <nav className="hidden items-center gap-1 sm:flex" aria-label="Business navigation">
                <a href="#dashboard" aria-current="page" className="rounded-md border-b-2 border-[#f2b93f] bg-[#202945] px-3 py-1.5 text-sm font-medium text-white">Dashboard</a>
                <a href="#bookings" className="px-2 py-1.5 text-sm text-[#b7c2df] hover:text-white">Bookings</a>
                <a href="#services" className="px-2 py-1.5 text-sm text-[#b7c2df] hover:text-white">Services</a>
                <a href="#settings" className="px-2 py-1.5 text-sm text-[#b7c2df] hover:text-white">Shop settings</a>
                <a href="#plan" className="px-2 py-1.5 text-sm text-[#b7c2df] hover:text-white">Plan</a>
              </nav>
            </div>
            <div className="ml-auto flex items-center gap-3 text-sm">
              <a href="#alerts" className="hidden text-[#b7c2df] hover:text-white sm:inline">Messages</a>
              <span className="text-[#b7c2df]">Noi</span>
              <button type="button" onClick={handleLogout} className="rounded-md border border-[#35405d] px-3 py-1.5 font-medium hover:bg-[#202945]">Log out</button>
            </div>
            <nav className="flex w-full gap-1 overflow-x-auto pb-0.5 sm:hidden" aria-label="Business navigation">
              <a href="#dashboard" aria-current="page" className="shrink-0 rounded-md border-b-2 border-[#f2b93f] bg-[#202945] px-3 py-1.5 text-sm font-medium">Dashboard</a>
              <a href="#bookings" className="shrink-0 px-2 py-1.5 text-sm text-[#b7c2df]">Bookings</a>
              <a href="#services" className="shrink-0 px-2 py-1.5 text-sm text-[#b7c2df]">Services</a>
              <a href="#settings" className="shrink-0 px-2 py-1.5 text-sm text-[#b7c2df]">Shop settings</a>
              <a href="#plan" className="shrink-0 px-2 py-1.5 text-sm text-[#b7c2df]">Plan</a>
            </nav>
          </div>
        </header>

        <div id="dashboard" className="mx-auto max-w-5xl px-5 pb-8 pt-7 sm:px-8 sm:pt-8">
          <div className="mb-5">
            <h1 className="text-3xl font-bold leading-tight tracking-tight sm:text-[40px]">Baan Suay Hair Studio</h1>
            <div className="mt-1 flex items-center gap-2 text-sm">
              <span className="rounded-full border border-[#29334f] bg-[#171e35] px-2.5 py-1 text-xs text-[#b7c2df]">Free plan</span>
              <a href="#public-page" className="text-[#b7c2df] underline underline-offset-2 hover:text-white">See your public page</a>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.55fr)_minmax(300px,1fr)] lg:gap-7">
            <section id="bookings" className="min-w-0">
              <h2 className="mb-3 text-lg font-semibold">Today&apos;s queue</h2>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
                {queue.map((item) => (
                  <div key={item.day} className={`min-h-[80px] rounded-lg border p-2.5 ${item.day === "Today" ? "border-[#c9d1e5] bg-[#171e35] ring-1 ring-[#c9d1e5]/50" : "border-[#303a58] bg-[#171e35]"}`}>
                    <p className="text-xs text-[#b7c2df]">{item.day}</p>
                    {item.closed ? <p className="mt-2 text-sm text-[#8792ae]">Closed</p> : <p className="mt-1 text-xl font-semibold leading-none">{item.count}<span className="ml-1 text-xs font-normal text-[#aebbd9]">/ {item.limit}</span></p>}
                    {!item.closed && <div className="mt-2 h-1 overflow-hidden rounded-full bg-[#202945]"><div className="h-full rounded-full bg-[#c2cbe0]" style={{ width: `${Math.max((item.count / item.limit) * 100, item.count ? 12 : 0)}%` }} /></div>}
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm leading-5 text-[#8792ae]">Each day shows bookings against a rough estimate of how many customers you can serve.</p>

              <div className="mt-5 space-y-3">
                <article className="grid overflow-hidden rounded-xl border border-[#29334f] bg-[#171e35] sm:grid-cols-[128px_minmax(0,1fr)]">
                  <div className="relative flex min-h-[112px] flex-col justify-center border-b-2 border-dashed border-[#0e1324] bg-[#202945] px-4 py-3 text-[#8792ae] sm:border-b-0 sm:border-r-2">
                    <span className="text-[27px] font-bold leading-none">16:00</span>
                    <span className="mt-2 text-sm">Wed 23 Sep</span>
                    <span className="mt-2 text-xs font-bold tracking-[0.12em]">W8LE3</span>
                  </div>
                  <div className="flex min-w-0 flex-col justify-center p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-semibold">Haircut and blow-dry</h3>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${bookingStates.first === "No-show" ? "bg-[#48231f] text-[#ff806c]" : "bg-[#123b34] text-[#38d3a5]"}`}>{bookingStates.first}</span>
                    </div>
                    <p className="mt-1 text-sm text-[#b7c2df]">Ton Kittisak, 089 876 5432</p>
                    <p className="mt-1 text-sm leading-5 text-[#b7c2df]">16:00–16:45. Deposit ฿135 kept by the shop.</p>
                  </div>
                </article>

                <article className="grid overflow-hidden rounded-xl border border-[#29334f] bg-[#171e35] sm:grid-cols-[128px_minmax(0,1fr)]">
                  <div className="relative flex min-h-[112px] flex-col justify-center border-b-2 border-dashed border-[#0e1324] bg-[#f2b93f] px-4 py-3 text-[#201a0c] sm:border-b-0 sm:border-r-2">
                    <span className="text-[27px] font-bold leading-none">17:30</span>
                    <span className="mt-2 text-sm">Wed 23 Sep</span>
                    <span className="mt-2 text-xs font-bold tracking-[0.12em]">Z5GA9</span>
                  </div>
                  <div className="flex min-w-0 flex-col justify-center p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-semibold">Hair spa treatment</h3>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${bookingStates.second === "Confirmed" ? "bg-[#123b34] text-[#38d3a5]" : "bg-[#202945] text-[#b7c2df]"}`}>{bookingStates.second}</span>
                    </div>
                    <p className="mt-1 text-sm text-[#b7c2df]">Ploy Srisuk, 081 234 5678</p>
                    <p className="mt-1 text-sm leading-5 text-[#b7c2df]">17:30–18:30. Deposit ฿270 paid, ฿630 at the shop.</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button type="button" onClick={() => updateBooking("second", "Completed")} className="rounded-md bg-[#e8ecf8] px-3 py-1.5 text-sm font-medium text-[#171e35] hover:bg-white">Mark completed</button>
                      <button type="button" onClick={() => updateBooking("second", "No-show")} className="rounded-md border border-[#35405d] px-3 py-1.5 text-sm font-medium hover:bg-[#202945]">No-show</button>
                    </div>
                  </div>
                </article>
              </div>
            </section>

            <aside className="space-y-4">
              <section id="plan" className="rounded-xl border border-[#29334f] bg-[#171e35] p-5">
                <h2 className="text-xl font-semibold">This month</h2>
                <p className="mt-3 flex items-baseline gap-2"><span className="text-4xl font-bold leading-none">8</span><span className="text-sm text-[#b7c2df]">of 10</span></p>
                <div className="mt-3 h-2 overflow-hidden rounded-full border border-[#303a58] bg-[#202945]"><div className="h-full w-4/5 bg-[#f2b93f]" /></div>
                <p className="mt-3 text-sm leading-5 text-[#b7c2df]">Bookings in September on the Free plan. 2 left.</p>
                <a href="#upgrade" className="mt-3 inline-flex rounded-md bg-[#f2b93f] px-3 py-1.5 text-sm font-medium text-[#201a0c] hover:bg-[#ffd063]">Upgrade to Pro for unlimited bookings</a>
              </section>

              <section id="alerts" className="rounded-xl border border-[#29334f] bg-[#171e35] p-5">
                <h2 className="text-xl font-semibold">Latest alerts</h2>
                <ul className="mt-3 divide-y divide-[#29334f] border-t border-[#29334f]">
                  {alerts.map((alert) => (
                    <li key={alert.title} className="flex gap-2.5 py-3">
                      <span className="mt-0.5 h-fit rounded bg-[#00c85a] px-1.5 py-0.5 text-[10px] font-bold leading-4 text-[#082116]">LINE</span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium leading-5">{alert.title}</p>
                        <p className="mt-0.5 text-sm text-[#aebbd9]">{alert.date}</p>
                      </div>
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-sm leading-5 text-[#8792ae]">2 reminders scheduled for you and your customers. <a href="#messages" className="underline underline-offset-2">All messages</a></p>
              </section>
            </aside>
          </div>
        </div>
      </main>
    </>
  );
}