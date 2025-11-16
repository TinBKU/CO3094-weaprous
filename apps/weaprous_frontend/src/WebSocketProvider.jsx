import React, { createContext, useEffect, useRef, useState, useCallback } from "react";

export const WebSocketContext = createContext(null);

export function WebSocketProvider({ wsPort, children }) {
    const [status, setStatus] = useState("idle");
    const [lastMessage, setLastMessage] = useState(null);
    const wsRef = useRef(null);

    useEffect(() => {
        console.log(wsPort)
        if (!wsPort) return; // chưa login → chưa kết nối WS

        let stopped = false;

        const wsHost = "127.0.0.1";
        const proto = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${proto}://${wsHost}:${wsPort}/ws`;

        console.log("[WS] Connecting:", url);

        function connect() {
            if (stopped) return;

            const ws = new WebSocket(url);
            wsRef.current = ws;
            setStatus("connecting");

            ws.onopen = () => {
                console.log("[WS] open");
                setStatus("connected");
            };

            ws.onclose = () => {
                console.log("[WS] close");
                setStatus("closed");
                if (!stopped) {
                    setTimeout(connect, 1500); // auto reconnect
                }
            };

            ws.onerror = (err) => {
                console.error("[WS] error:", err);
                setStatus("error");
            };

            ws.onmessage = (ev) => {
                try {
                    const obj = JSON.parse(ev.data);
                    setLastMessage(obj);
                } catch (e) {
                    console.error("[WS] parse error:", e);
                }
            };
        }

        connect();

        return () => {
            stopped = true;
            if (wsRef.current) wsRef.current.close();
        };
    }, [wsPort]);

    const closeWS = () => {
        if (wsRef.current) {
            try { wsRef.current.close(); } catch (e) { }
        }
        wsRef.current = null;
    };

    const send = useCallback((obj) => {
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(obj));
        } else {
            console.warn("[WS] cannot send, WS not open:", obj);
        }
    }, []);

    const value = {
        status,
        lastMessage,
        send,
        closeWS
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
}
