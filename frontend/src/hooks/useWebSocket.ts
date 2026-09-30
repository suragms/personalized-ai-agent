import { useEffect, useRef } from "react";
import { API_BASE, getAccess } from "@/lib/api";

export function useWebSocket(path: string, onMessage: (data: any) => void) {
  const savedHandler = useRef(onMessage);
  savedHandler.current = onMessage;

  useEffect(() => {
    const token = getAccess();
    if (!token) return;

    // Same-origin (dev via Vite proxy), or the configured backend origin.
    let wsUrl: string;
    if (API_BASE) {
      const base = new URL(API_BASE);
      base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${base.origin}${path}?token=${encodeURIComponent(token)}`;
    } else {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${protocol}//${window.location.host}${path}?token=${encodeURIComponent(token)}`;
    }

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        savedHandler.current(data);
      } catch (e) {
        console.error("Failed to parse WS message", e);
      }
    };

    return () => {
      ws.close();
    };
  }, [path]);
}
