import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";

import { api } from "@/lib/api";

export default function Register() {
  const router = useRouter();
  const [role, setRole] = useState("customer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const payload = {
      email: formData.get("email"),
      password: "demo1234",
      full_name: formData.get("full_name"),
      role,
    };
    if (role === "business") payload.business_name = formData.get("business_name");

    try {
      const user = await api("/api/auth/register", { method: "POST", body: payload });
      router.push(user.role === "business" ? "/dashboard" : "/");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Head>
        <title>Sign up | Nadd</title>
      </Head>
      <main className="flex min-h-screen flex-col bg-[#0e1324] text-[#e8ecf8]">
        <header className="border-b border-[#26304b] bg-[#171e35]">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3 sm:px-8">
            <div className="flex items-center gap-7">
              <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
                Nadd <span className="rounded bg-[#f2b93f] px-1.5 py-0.5 text-xs font-bold text-[#201a0c]">นัด</span>
              </Link>
              <Link href="/" className="hidden text-sm text-[#b7c2df] sm:inline">Find a shop</Link>
            </div>
            <nav className="flex items-center gap-2" aria-label="Account navigation">
              <Link href="/login" className="rounded-md border border-[#35405d] px-3 py-1.5 text-sm font-medium hover:bg-[#202945]">Log in</Link>
              <span aria-current="page" className="rounded-md bg-[#e8ecf8] px-3 py-1.5 text-sm font-semibold text-[#171e35]">Sign up</span>
            </nav>
          </div>
        </header>

        <div className="mx-auto grid w-full max-w-5xl flex-1 content-start gap-8 px-5 py-8 sm:px-8 sm:py-10 md:grid-cols-[438px_minmax(0,1fr)] md:gap-7 md:py-8">
          <section className="h-fit rounded-xl border border-[#29334f] bg-[#171e35] p-5 sm:p-5">
            <h1 className="text-[30px] font-semibold leading-tight tracking-tight">Create an account</h1>
            <div className="mt-3 inline-flex overflow-hidden rounded-md border border-[#35405d]" role="group" aria-label="Choose account type">
              <button type="button" aria-pressed={role === "customer"} onClick={() => setRole("customer")} className={`px-3.5 py-2 text-sm ${role === "customer" ? "bg-[#e8ecf8] text-[#171e35]" : "bg-[#171e35] text-[#b7c2df] hover:bg-[#202945]"}`}>
                I&apos;m booking
              </button>
              <button type="button" aria-pressed={role === "business"} onClick={() => setRole("business")} className={`border-l border-[#35405d] px-3.5 py-2 text-sm ${role === "business" ? "bg-[#e8ecf8] text-[#171e35]" : "bg-[#171e35] text-[#b7c2df] hover:bg-[#202945]"}`}>
                I run a shop
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
              <label className="block space-y-1.5 text-sm font-medium">
                <span>Your name</span>
                <input name="full_name" autoComplete="name" required minLength={1} className="h-11 w-full rounded-md border border-[#35405d] bg-[#171e35] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
              </label>
              {role === "business" && (
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>Shop name</span>
                  <input name="business_name" required className="h-11 w-full rounded-md border border-[#35405d] bg-[#171e35] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
                </label>
              )}
              <div className="grid grid-cols-2 gap-3">
                <label className="block min-w-0 space-y-1.5 text-sm font-medium">
                  <span>Email</span>
                  <input name="email" type="email" autoComplete="email" required className="h-11 w-full rounded-md border border-[#35405d] bg-[#171e35] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
                </label>
                <label className="block min-w-0 space-y-1.5 text-sm font-medium">
                  <span>Phone</span>
                  <input name="phone" type="tel" autoComplete="tel" className="h-11 w-full rounded-md border border-[#35405d] bg-[#171e35] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
                </label>
              </div>
              <label className="flex items-center gap-2.5 py-0.5 text-sm">
                <input name="line_alerts" type="checkbox" defaultChecked className="h-4 w-4 accent-[#e8ecf8]" />
                <span>Send my alerts and reminders on LINE</span>
              </label>

              {error && <p role="alert" className="text-sm text-[#ff9585]">{error}</p>}
              <button type="submit" disabled={loading} className="h-[38px] w-full rounded-md bg-[#e8ecf8] px-4 text-sm font-semibold text-[#171e35] hover:bg-white disabled:cursor-wait disabled:opacity-60">
                {loading ? "Creating account..." : "Create account"}
              </button>
            </form>

            <p className="mt-3 text-sm leading-5 text-[#8792ae]">Prototype: every account logs in with the password <code className="rounded bg-[#202945] px-1.5 py-0.5 text-xs text-[#b7c2df]">demo1234</code>, so don&apos;t use a real one.</p>
            <p className="mt-3 text-sm text-[#aebbd9]">Already have an account? <Link href="/login" className="underline underline-offset-4">Log in</Link></p>
          </section>

          <aside className="max-w-md pt-1 md:pt-5">
            <h2 className="text-xl font-semibold text-[#b7c2df]">{role === "customer" ? "For customers" : "For shop owners"}</h2>
            <p className="mt-3 text-base leading-6 text-[#b7c2df]">
              {role === "customer"
                ? "Book a time in under a minute, pay a small deposit by PromptPay, and get a reminder before you go. You pay the rest at the shop."
                : "Bring your bookings together, set up your services, and keep customers informed with timely reminders."}
            </p>
          </aside>
        </div>

        <footer className="border-t border-[#26304b]">
          <div className="mx-auto max-w-5xl px-5 py-5 text-sm leading-5 text-[#8792ae] sm:px-8">
            <p className="max-w-2xl">Nadd is a course prototype of an SME booking system. Payments run in test mode, and LINE and email messages are shown inside the app instead of being sent.</p>
            <p className="mt-1 max-w-2xl">Changes are saved to this page&apos;s shared database, so everyone who opens the link sees the same shops and bookings.</p>
          </div>
        </footer>
      </main>
    </>
  );
}
