// src/useWebSocket.js
import { useContext } from "react";
import { WebSocketContext } from "./WebSocketProvider";

export function useWebSocket() {
    return useContext(WebSocketContext);
}
