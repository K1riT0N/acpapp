// Who is logged in, shared with every page through React context.
// The token lives in localStorage ("nadd.token"); on page load we ask the API who it belongs to.
import { useRouter } from "next/router";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { useToast } from "@/components/Toasts";

import { api, getToken, setToken } from "./api";

const AuthContext = createContext({ user: null, ready: false });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false); // false until we know whether someone is logged in

  useEffect(() => {
    if (!getToken()) {
      setReady(true);
      return;
    }
    api("/auth/me")
      .then(setUser)
      .catch(() => setToken(null)) // expired or invalid token: treat as logged out
      .finally(() => setReady(true));
  }, []);

  // Called with the {token, user} that /auth/login and /auth/register return
  const signIn = useCallback(({ token, user }) => {
    setToken(token);
    setUser(user);
  }, []);

  const signOut = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, ready, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

// Link to the login page that comes back to `path` afterwards, e.g. /login?next=%2Fshops%2Fabc
export function loginHref(path) {
  return path && path !== "/" && !path.startsWith("/login") && !path.startsWith("/signup")
    ? `/login?next=${encodeURIComponent(path)}`
    : "/login";
}

// After logging in: go back to where the person came from (?next=...), or to their home page.
// Owners are never sent to customer-only pages such as booking or paying.
export function useAfterLogin() {
  const router = useRouter();
  const toast = useToast();
  const { signIn } = useAuth();
  return (result) => {
    signIn(result);
    toast("Logged in as " + result.user.full_name + ".");
    const next = typeof router.query.next === "string" ? router.query.next : "";
    const ownerBad = result.user.role === "shop_owner" && /^\/(book|pay|my)(\/|$)/.test(next);
    if (next.startsWith("/") && !next.startsWith("//") && next !== "/" && !ownerBad) router.push(next);
    else router.push(result.user.role === "shop_owner" ? "/owner" : "/");
  };
}
