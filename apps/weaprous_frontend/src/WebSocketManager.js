// src/WebSocketManager.js
export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.url = null;
        this.listeners = new Set();
        this.statusListeners = new Set();
    }

    initFromLocation(defaultPort = 7000) {
        if (this.url) return; // chỉ set 1 lần
        const search = new URLSearchParams(window.location.search);
        const wsPort = search.get("ws") || defaultPort;
        const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
        this.url = `${wsProto}://${window.location.hostname}:${wsPort}/ws`;
    }

    connect() {
        if (this.ws || !this.url) return; // đã có WS hoặc chưa init url

        console.log("[WSManager] Connecting to", this.url);
        const ws = new WebSocket(this.url);
        this.ws = ws;

        ws.onopen = () => {
            console.log("[WSManager] OPEN");
            this._notifyStatus("connected");
            this.send({ cmd: "list_peers" });
        };

        ws.onclose = () => {
            console.log("[WSManager] CLOSED, will reconnect");
            this._notifyStatus("closed");
            this.ws = null;
            setTimeout(() => this.connect(), 2000);
        };

        ws.onerror = (err) => {
            console.error("[WSManager] ERROR", err);
            this._notifyStatus("error");
        };

        ws.onmessage = (ev) => {
            try {
                const obj = JSON.parse(ev.data);
                // notify all subscribers in React
                for (const cb of this.listeners) cb(obj);
            } catch (e) {
                console.error("[WSManager] parse error", e);
            }
        };
    }

    send(obj) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log("[WSManager] send:", obj);
            this.ws.send(JSON.stringify(obj));
        }
    }

    // React component đăng ký nghe message
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    subscribeStatus(listener) {
        this.statusListeners.add(listener);
        return () => this.statusListeners.delete(listener);
    }

    _notifyStatus(status) {
        for (const cb of this.statusListeners) cb(status);
    }

    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// singleton dùng toàn app
export const wsManager = new WebSocketManager();
