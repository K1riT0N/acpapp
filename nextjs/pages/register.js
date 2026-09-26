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
      password: formData.get("password"),
      full_name: formData.get("full_name"),
      role,
    };
    if (role === "business") payload.business_name = formData.get("business_name");

    try {
      await api("/api/auth/register", { method: "POST", body: payload });
      router.push("/");
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
      <main className="min-h-screen bg-[#0e1324] px-5 py-8 text-[#e8ecf8]">
        <div className="mx-auto max-w-5xl">
          <Link href="/" className="inline-flex items-center gap-2 text-xl font-bold">
            Nadd <span className="rounded bg-[#f2b93f] px-1.5 py-0.5 text-xs font-bold text-[#201a0c]">นัด</span>
          </Link>
          <section className="mx-auto mt-10 max-w-md border border-[#29334f] bg-[#141a2e] p-6 sm:mt-14 sm:p-8">
            <h1 className="text-2xl font-semibold">Create your account</h1>
            <p className="mt-2 text-sm leading-6 text-[#aebbd9]">Join Nadd to manage bookings or keep track of your appointments.</p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label className="block space-y-1.5 text-sm font-medium">
                <span>Full name</span>
                <input name="full_name" autoComplete="name" required minLength={1} className="h-10 w-full rounded-md border border-[#35405d] bg-[#0e1324] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                <span>Email</span>
                <input name="email" type="email" autoComplete="email" required className="h-10 w-full rounded-md border border-[#35405d] bg-[#0e1324] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                <span>Password</span>
                <input name="password" type="password" autoComplete="new-password" required minLength={8} className="h-10 w-full rounded-md border border-[#35405d] bg-[#0e1324] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
                <span className="block text-xs font-normal text-[#8792ae]">At least 8 characters</span>
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                <span>Account type</span>
                <select value={role} onChange={(event) => setRole(event.target.value)} className="h-10 w-full rounded-md border border-[#35405d] bg-[#0e1324] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]">
                  <option value="customer">Customer</option>
                  <option value="business">Business</option>
                </select>
              </label>
              {role === "business" && (
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>Business name</span>
                  <input name="business_name" required className="h-10 w-full rounded-md border border-[#35405d] bg-[#0e1324] px-3 text-[#e8ecf8] outline-none focus:border-[#f2b93f]" />
                </label>
              )}

              {error && <p role="alert" className="text-sm text-[#ff9585]">{error}</p>}
              <button type="submit" disabled={loading} className="h-10 w-full rounded-md bg-[#f2b93f] px-4 text-sm font-semibold text-[#201a0c] hover:bg-[#ffd063] disabled:cursor-wait disabled:opacity-60">
                {loading ? "Creating account..." : "Sign up"}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-[#aebbd9]">
              Already have an account? <Link href="/login" className="font-semibold text-white underline underline-offset-4">Log in</Link>
            </p>
          </section>
        </div>
      </main>
    </>
  );
}
