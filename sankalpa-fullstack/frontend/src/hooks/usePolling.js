import { useEffect } from "react";

const DEFAULT_MS = Number(import.meta.env.VITE_POLL_INTERVAL_MS) || 5000;

export function usePolling(callback, intervalMs = DEFAULT_MS, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined;
    callback();
    const id = setInterval(callback, intervalMs);
    return () => clearInterval(id);
  }, [callback, intervalMs, enabled]);
}
