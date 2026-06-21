import { useState, useEffect, useRef } from 'react';

export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    if (!url) return;

    function connect() {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log(`WebSocket Connected: ${url}`);
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          console.error("Failed to parse WebSocket message", e);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000;
          console.log(`WebSocket Disconnected. Reconnecting in ${timeout}ms...`);
          setTimeout(connect, timeout);
          reconnectAttempts.current += 1;
        } else {
          console.error("Max reconnect attempts reached.");
        }
      };

      ws.current.onerror = (err) => {
        console.error("WebSocket Error:", err);
        ws.current.close();
      };
    }

    connect();

    return () => {
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect loop on unmount
        ws.current.close();
      }
    };
  }, [url]);

  return { isConnected, lastMessage };
}
