// The logged-in user's messages, shared by the header badge and the Messages page.
// Re-fetched every 15 seconds ("live" updates). A toast announces a message that was sent within the last
// 2 minutes and that this browser hasn't seen yet, like the prototype's checkAlerts().
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import { useToast } from "@/components/Toasts";
import { api } from "./api";
import { useAuth } from "./auth";

const POLL_MS = 15000;
const ALERT_WINDOW_MS = 2 * 60 * 1000;

const MessagesContext = createContext({ inbox: null, reload: () => Promise.resolve() });

export function MessagesProvider({ children }) {
  const { user } = useAuth();
  const toast = useToast();
  const [inbox, setInbox] = useState(null);
  const seen = useRef(new Set());
  const primed = useRef(false); // the first load only remembers what's there, without toasts

  const reload = useCallback(() => {
    if (!user) return Promise.resolve();
    return api("/notifications/me")
      .then((data) => {
        data.sent.forEach((n) => {
          if (seen.current.has(n.notification_id)) return;
          seen.current.add(n.notification_id);
          if (primed.current && Date.now() - Date.parse(n.sent_at) < ALERT_WINDOW_MS) {
            toast("New " + (n.channel === "line" ? "LINE" : "email") + " message: " + n.title);
          }
        });
        primed.current = true;
        setInbox(data);
        return data;
      })
      .catch(() => null);
  }, [user, toast]);

  useEffect(() => {
    // A different person logged in (or out): start again
    seen.current = new Set();
    primed.current = false;
    setInbox(null);
    if (!user) return;
    reload();
    const t = setInterval(reload, POLL_MS);
    return () => clearInterval(t);
  }, [user, reload]);

  return <MessagesContext.Provider value={{ inbox, reload }}>{children}</MessagesContext.Provider>;
}

export function useMessages() {
  return useContext(MessagesContext);
}
