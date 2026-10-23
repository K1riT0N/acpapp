// Top bar. The links change with who is logged in: a visitor, a customer or a shop owner.
import Link from "next/link";
import { useRouter } from "next/router";

import { loginHref, useAuth } from "@/lib/auth";
import { useMessages } from "@/lib/messages";
import { useToast } from "@/components/Toasts";

function NavLink({ href, on, children }) {
  return (
    <Link href={href} className="nav-a" aria-current={on ? "page" : undefined}>
      {children}
    </Link>
  );
}

export default function Header() {
  const router = useRouter();
  const { user, ready, signOut } = useAuth();
  const toast = useToast();
  const { inbox } = useMessages();
  const unread = inbox?.unread_count || 0;
  const p = router.pathname;
  const shopping = p === "/" || p.startsWith("/shops") || p.startsWith("/book/");

  function logout() {
    signOut();
    toast("You're logged out.");
    router.push("/");
  }

  let links;
  if (!user) {
    links = <NavLink href="/" on={shopping}>Find a shop</NavLink>;
  } else if (user.role === "customer") {
    links = (
      <>
        <NavLink href="/" on={shopping}>Find a shop</NavLink>
        <NavLink href="/my" on={p === "/my" || p.startsWith("/bookings/") || p.startsWith("/pay/")}>My bookings</NavLink>
      </>
    );
  } else {
    links = (
      <>
        <NavLink href="/owner" on={p === "/owner"}>Dashboard</NavLink>
        <NavLink href="/owner/bookings" on={p === "/owner/bookings" || p.startsWith("/bookings/")}>Bookings</NavLink>
        <NavLink href="/owner/services" on={p === "/owner/services"}>Services</NavLink>
        <NavLink href="/owner/settings" on={p === "/owner/settings"}>Shop settings</NavLink>
        <NavLink href="/owner/plan" on={p === "/owner/plan"}>Plan</NavLink>
      </>
    );
  }

  let right = null;
  if (user) {
    right = (
      <>
        <NavLink href="/inbox" on={p === "/inbox"}>
          Messages
          {unread > 0 && <span className="badge" aria-label={unread + " unread"}>{unread}</span>}
        </NavLink>
        <span className="who">{String(user.full_name || "").split(" ")[0]}</span>
        <button className="btn small" onClick={logout}>Log out</button>
      </>
    );
  } else if (ready) {
    right = (
      <>
        <Link className="btn small" href={loginHref(router.asPath)}>Log in</Link>
        <Link className="btn small primary" href="/signup">Sign up</Link>
      </>
    );
  }

  return (
    <header className="bar">
      <div className="bar-in">
        <Link className="brand" href="/">
          Nadd <small lang="th">นัด</small>
        </Link>
        <nav className="nav" aria-label="Main">{links}</nav>
        <div className="bar-right">{right}</div>
      </div>
    </header>
  );
}
