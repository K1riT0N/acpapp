// Short messages at the bottom of the screen ("Service saved."), like the prototype's toast().
// Any component can call: const toast = useToast(); toast("Service saved.");
import { createContext, useCallback, useContext, useRef, useState } from "react";

const ToastContext = createContext(() => {});
const MAX_TOASTS = 3;
const TOAST_MS = 5000;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(1);

  const toast = useCallback((text) => {
    const id = nextId.current++;
    setToasts((list) => [...list, { id, text }].slice(-MAX_TOASTS));
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), TOAST_MS);
  }, []);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div id="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className="toast" role="status">
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
