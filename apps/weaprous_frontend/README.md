# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc]
# ChatApp Frontend (React + WebSocket + Cookie Auth)

Giao diện chat mô phỏng Zalo, kết nối WebSocket bảo mật bằng session cookie từ **cookie_http_server**.

---

## 🚀 Tính năng chính

- 🔐 **Đăng nhập + session cookie**
- 🔌 **WebSocket bảo mật** (middleware `/whoami`)
- 👥 **Danh sách peers – Auto-connect**
- 💬 **Chat nhóm & chat 1–1 (DM)**
- 🔔 **Unread badge** mỗi channel
- 🎯 **Tự động mở đúng WebSocket port đã đăng ký**

---

## 📂 Cấu trúc thư mục

```
src/
  App.jsx
  index.css
  WebSocketProvider.jsx
  useWebSocket.js
  routes/
    LoginPage.jsx
    ChatPage.jsx
  components/
    SidebarPeers.jsx
    ChannelPanel.jsx
    ChatWindow.jsx
public/
```

---

## 🛠 Cài đặt & chạy

```bash
npm install
npm run dev
```

Ứng dụng chạy tại:

```
http://localhost:5173
```

---

## 🔧 Yêu cầu Backend

Chạy đủ 3 service:

| Service | File | Port |
|--------|------|-------|
| Cookie Server | `start_sampleapp.py` | 9000 |
| Tracker | `tracker_server.py` | 5000 |
| Peer Web | `peer_client.py` | 7000 / 7001 / ... |

---

## 🔑 Luồng hoạt động

1. User login → nhận `session=<sid>`
2. FE fetch `/whoami` → nhận `{user, peer_id, ws_port}`
3. FE mở WS:  
   ```
   ws://127.0.0.1:<ws_port>/ws
   ```
4. Chat nhóm hoặc 1–1 tùy chọn
5. Thoát → `/logout`

---

## 📝 License

MIT License
(https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
