// src/pages/ChatPage.jsx
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { WebSocketProvider } from "../WebSocketProvider";
import { useWebSocket } from "../useWebSocket";

import SidebarPeers from "../components/SidebarPeers";
import ChannelPanel from "../components/ChannelPanel";
import ChatWindow from "../components/ChatWindow";

function ChatInner({ auth }) {
    const { status: wsStatus, lastMessage, send, closeWS } = useWebSocket();
    const [meId, setMeId] = useState(auth?.peerId || auth?.user || "unknown");
    const [peers, setPeers] = useState({});
    const [connections, setConnections] = useState(new Set());
    const [joinedChannels, setJoinedChannels] = useState(new Set(["general"]));
    const [currentChannel, setCurrentChannel] = useState("general");
    const [messagesByChannel, setMessagesByChannel] = useState({});
    const [autoConnected, setAutoConnected] = useState(false);
    const [readCountByChannel, setReadCountByChannel] = useState({});
    const navigate = useNavigate();

    // helper: nhét message vào state
    const pushMessage = useCallback((msg) => {
        const ch = msg.channel || "general";

        setMessagesByChannel((prev) => {
            const list = prev[ch] || [];
            return {
                ...prev,
                [ch]: [...list, msg],
            };
        });
    }, []);

    // Tạo tên phòng DM cố định
    const makeDmChannel = useCallback((a, b) => {
        const arr = [a || "", b || ""].sort();
        return `dm:${arr[0]}:${arr[1]}`;
    }, []);

    // Click vào peer → connect + tạo/join room DM
    const handleStartChatWithPeer = (peerId) => {
        if (!peerId) return;

        const room = makeDmChannel(meId, peerId); // vd: dm:peerA:peerB

        setJoinedChannels((old) => {
            const s = new Set(old);
            s.add(room);
            return s;
        });
        setCurrentChannel(room);

        if (wsStatus === "connected") {
            send({ cmd: "connect", peer_id: peerId });
            send({ cmd: "create_room", channel: room, to_peer: peerId });
        }
    };

    // Xử lý message từ backend
    useEffect(() => {
        if (!lastMessage) return;
        console.log("[ChatPage] WS:", lastMessage);

        if (lastMessage.type === "connected") {
            if (lastMessage.peer_id && meId === "unknown") {
                setMeId(lastMessage.peer_id);
            }
            return;
        }

        if (lastMessage.type === "peers") {
            const p = lastMessage.peers || {};
            setPeers(p);

            // AUTO-CONNECT: chỉ làm 1 lần
            if (!autoConnected && wsStatus === "connected") {
                const ids = Object.keys(p);
                console.log("[Chat] auto-connect peers:", ids);
                ids.forEach((pid) => {
                    send({ cmd: "connect", peer_id: pid });
                });
                setAutoConnected(true);
            }
            return;
        }

        // Các loại message chat
        if (
            lastMessage.type === "msg" ||
            lastMessage.type === "message" ||
            lastMessage.payload
        ) {
            const p = lastMessage.payload || lastMessage;
            const ch = p.channel || "general";
            const msg = {
                channel: ch,
                from: p.from || p.peer_id || "unknown",
                text: p.text || p.msg || JSON.stringify(p),
                ts: p.ts || Date.now() / 1000,
            };

            setJoinedChannels((old) => {
                if (old.has(ch)) return old;
                const s = new Set(old);
                s.add(ch);
                return s;
            });

            pushMessage(msg);
            return;
        }

        if (lastMessage.type === "joined_channel") {
            const ch = lastMessage.channel;
            if (ch === "__meta__") return;
            setJoinedChannels((old) => {
                const s = new Set(old);
                s.add(ch);
                return s;
            });
            return;
        }

        if (lastMessage.type === "peer_connected") {
            setConnections((old) => {
                const s = new Set(old);
                s.add(lastMessage.peer_id);
                return s;
            });
            return;
        }

        if (lastMessage.type === "peer_disconnected") {
            setConnections((old) => {
                const s = new Set(old);
                s.delete(lastMessage.peer_id);
                return s;
            });
            return;
        }

        if (lastMessage.type === "connect_result") {
            if (!lastMessage.ok) {
                alert("Connect failed: " + lastMessage.info);
            }
            return;
        }
    }, [lastMessage, meId, pushMessage, autoConnected, wsStatus, send]);

    // ✅ Mỗi lần đổi kênh HOẶC tin trong kênh hiện tại thay đổi
    // => đánh dấu số tin đã đọc của kênh hiện tại = tổng số tin
    useEffect(() => {
        setReadCountByChannel((prev) => {
            const total = (messagesByChannel[currentChannel] || []).length;
            if (prev[currentChannel] === total) return prev; // tối ưu nhỏ
            return {
                ...prev,
                [currentChannel]: total,
            };
        });
    }, [currentChannel, messagesByChannel]);

    // ✅ Tính unreadByChannel từ messagesByChannel + readCountByChannel
    const unreadByChannel = useMemo(() => {
        const res = {};

        // theo messages thực tế
        Object.entries(messagesByChannel).forEach(([ch, list]) => {
            const total = list.length;
            const read = readCountByChannel[ch] || 0;
            res[ch] = Math.max(0, total - read);
        });

        // đảm bảo kênh đã join nhưng chưa có tin cũng có key = 0
        joinedChannels.forEach((ch) => {
            if (res[ch] == null) res[ch] = 0;
        });

        return res;
    }, [messagesByChannel, readCountByChannel, joinedChannels]);

    const messages = messagesByChannel[currentChannel] || [];

    const handleSendMessage = (text) => {
        if (!text.trim()) return;
        if (wsStatus !== "connected") {
            console.warn("WS chưa connected");
            return;
        }
        send({ cmd: "broadcast", channel: currentChannel, text });
    };

    const handleConnectPeer = (peerId) => {
        if (wsStatus !== "connected") return;
        send({ cmd: "connect", peer_id: peerId });
    };

    const handleRefreshPeers = () => {
        if (wsStatus !== "connected") return;
        send({ cmd: "list_peers" });
    };

    // ✅ Tạo phòng mới
    const handleCreateChannel = (room) => {
        if (!room) return;
        if (wsStatus === "connected") {
            console.log("[handleCreateChannel]:", room);
            send({ cmd: "create_room", channel: room });
        }
        setJoinedChannels((old) => {
            const s = new Set(old);
            s.add(room);
            return s;
        });
        setCurrentChannel(room); // hiện phòng vừa tạo → effect trên sẽ reset readCount
    };

    // ✅ Chọn kênh: chỉ đổi kênh + join, không tự đụng vào unread nữa
    const handleSelectChannel = (ch) => {
        setCurrentChannel(ch);
        if (wsStatus === "connected") {
            if (ch === "__meta__") return;
            send({ cmd: "join", channel: ch });
        }
    };

    const handleAutoConnect = () => {
        if (wsStatus !== "connected") return;
        Object.keys(peers).forEach((pid) =>
            send({ cmd: "connect", peer_id: pid })
        );
    };

    const handleClearMessages = () => {
        setMessagesByChannel({});
        setReadCountByChannel({});
    };

    useEffect(() => {
        if (wsStatus === "connected" && !autoConnected) {
            console.log("[Chat] WS connected, requesting peers...");
            send({ cmd: "list_peers" });
        }
    }, [wsStatus, autoConnected, send]);

    const firstLetter =
        meId && meId !== "unknown" ? meId[0].toUpperCase() : "U";

    const handleLogout = async () => {
        try {
            await fetch("http://127.0.0.1:9000/logout", {
                method: "POST",
                credentials: "include",
            });
        } catch (e) {
            console.error("logout error", e);
        }

        clearAuth();        // Xóa localStorage auth
        closeWS();          // Đóng WebSocket

        navigate("/login"); // Trở về trang login
    };

    const clearAuth = () => {
        localStorage.removeItem("auth");
    }

    return (
        <div className="app-root">
            {/* LEFT SIDEBAR */}
            <div className="sidebar-left">
                <div className="avatar-circle">{firstLetter}</div>
                {meId}
                <div className="sidebar-left-icons">
                    {/* icon ... */}
                </div>

                <div style={{ marginTop: "auto", paddingBottom: 16 }}>
                    <button
                        onClick={handleLogout}
                        style={{
                            padding: "6px 10px",
                            fontSize: 12,
                            borderRadius: 8,
                            border: "1px solid #e5e7eb",
                            cursor: "pointer",
                            background: "#fff",
                        }}
                    >
                        Logout
                    </button>

                    <div className="sidebar-left-status">
                        WS: {wsStatus}
                    </div>
                </div>
            </div>

            {/* MIDDLE PANEL */}
            <div className="middle-panel">
                <div className="middle-header">
                    <span className="middle-title">Tin nhắn</span>
                    <button className="refresh-btn" onClick={handleRefreshPeers}>
                        Refresh
                    </button>
                </div>

                <div className="search-wrapper">
                    <input className="search-input" placeholder="Tìm kiếm..." />
                </div>

                <SidebarPeers
                    peers={peers}
                    meId={meId}
                    wsStatus={wsStatus}
                    onConnectPeer={handleConnectPeer}
                    onRefreshPeers={handleRefreshPeers}
                    onAutoConnect={handleAutoConnect}
                    onStartChat={handleStartChatWithPeer}
                />

                <ChannelPanel
                    currentChannel={currentChannel}
                    joinedChannels={joinedChannels}
                    unreadByChannel={unreadByChannel}
                    onSelectChannel={handleSelectChannel}
                    onCreateChannel={handleCreateChannel}
                />
            </div>

            {/* RIGHT PANEL */}
            <ChatWindow
                currentChannel={currentChannel}
                messages={messages}
                meId={meId}
                onSend={handleSendMessage}
                connectionsCount={connections.size}
                onClearMessages={handleClearMessages}
            />
        </div>
    );
}

function ChatPage() {
    const navigate = useNavigate();
    const [auth, setAuth] = useState(null);
    useEffect(() => {
        try {
            const raw = localStorage.getItem("chatAuth");
            if (!raw) {
                navigate("/login");
                return;
            }
            const parsed = JSON.parse(raw);
            if (!parsed || !parsed.wsPort) {
                navigate("/login");
                return;
            }
            setAuth(parsed);
        } catch {
            navigate("/login");
        }
    }, [navigate]);

    if (!auth) return null; // đang redirect hoặc chưa load xong

    console.log("ChatPage auth =", auth); // bạn có thể check wsPort ở đây

    return (
        <WebSocketProvider wsPort={auth.wsPort}>
            <ChatInner auth={auth} />
        </WebSocketProvider>
    );
}

export default ChatPage;
