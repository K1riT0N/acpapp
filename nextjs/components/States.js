// Page states shared by many pages: loading, not found, please log in, wrong kind of account.
// Wording follows the prototype's vNotFound, loginPrompt and notFor.
import Link from "next/link";
import { useRouter } from "next/router";

import { loginHref, useAuth } from "@/lib/auth";

export function Loading({ text = "Loading…" }) {
  return <div className="loading">{text}</div>;
}

export function NotFound({ message = "We couldn't find that page." }) {
  return (
    <div className="empty-state">
      <h1>{message}</h1>
      <Link className="btn" href="/">Back to all shops</Link>
    </div>
  );
}

export function LoginPrompt({ message }) {
  const router = useRouter();
  return (
    <div className="empty-state">
      <h1>{message}</h1>
      <div className="row">
        <Link className="btn primary" href={loginHref(router.asPath)}>Log in</Link>
        <Link className="btn" href="/signup">Create an account</Link>
      </div>
    </div>
  );
}

export function NotFor({ role }) {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const customer = role === "customer";
  return (
    <div className="empty-state">
      <h1>{customer ? "This page is for customers." : "This page is for shop owners."}</h1>
      <p className="lede">
        You&apos;re logged in as {user?.full_name}. Log out, then log in with a {customer ? "customer" : "shop owner"} account.
      </p>
      <button className="btn" onClick={() => { signOut(); router.push("/login"); }}>Log out</button>
    </div>
  );
}

export function ErrorText({ error }) {
  return error ? <p className="err" role="alert">{error}</p> : null;
}
