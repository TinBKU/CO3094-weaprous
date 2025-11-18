// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import ChatPage from "./pages/ChatPage";
import { WebSocketProvider } from "./WebSocketProvider";

function App() {
  // Lấy wsPort từ localStorage để truyền vào WebSocketProvider
  let wsPort = null;
  try {
    const auth = JSON.parse(localStorage.getItem("chatAuth") || "null");
    wsPort = auth?.wsPort || null;
  } catch {
    wsPort = null;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
