import { useEffect, useRef } from "react";
import { getAccess } from "@/lib/api";

export function useWebSocket(path: string, onMessage: (data: any) => void) {
  const savedHandler = useRef(onMessage);
  savedHandler.current = onMessage;

  useEffect(() => {
    const token = getAccess();
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}${path}?token=${token}`;

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
