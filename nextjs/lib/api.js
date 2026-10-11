// One place for every call to the back-end.
// If the user is logged in, the login token is sent in the Authorization header.
import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "nadd.token";

// localStorage can be missing (server rendering) or blocked (private mode), so always wrap it
export function getToken() {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch (e) {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch (e) {}
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new Error("Can't reach the Nadd server. Check your connection and try again.");
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.detail || `Request failed with status ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// Load data for a page: const { data, error, reload } = useApi("/shops/abc").
// Pass null as the path to wait (for example until the user is known).
// keepPrevious: when the path changes, keep showing the old data until the new data arrives (no "Loading…" flash).
export function useApi(path, { keepPrevious = false } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path });

  const load = useCallback(() => {
    if (!path) return Promise.resolve();
    return api(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState((s) => ({ data: s.data, error, loading: false })));
  }, [path]);

  useEffect(() => {
    setState((s) => ({ data: keepPrevious ? s.data : null, error: null, loading: !!path }));
    load();
  }, [load, path, keepPrevious]);

  return { ...state, reload: load, setData: (data) => setState((s) => ({ ...s, data })) };
}

// Run `fn` every `ms` milliseconds while the page is open ("live" updates for owner pages and messages)
export function usePoll(fn, ms = 15000) {
  useEffect(() => {
    const t = setInterval(fn, ms);
    return () => clearInterval(t);
  }, [fn, ms]);
}
