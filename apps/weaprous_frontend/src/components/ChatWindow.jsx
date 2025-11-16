// src/components/ChatWindow.jsx
import React, { useState } from "react";

function ChatWindow({
    currentChannel,
    messages,
    meId,
    onSend,
    connectionsCount = 0,
}) {
    const [input, setInput] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        const text = input.trim();
        if (!text) return;
        onSend && onSend(text);
        setInput("");
    };

    // Format timestamp -> "HH:MM"
    const formatTime = (ts) => {
        if (!ts) return "";
        const d = new Date(ts * 1000);
        const hh = d.getHours().toString().padStart(2, "0");
        const mm = d.getMinutes().toString().padStart(2, "0");
        return `${hh}:${mm}`;
    };

    // Default avatar when no image
    const getAvatar = (username) => {
        // Nếu muốn có ảnh random đẹp:
        // return `https://api.dicebear.com/7.x/thumbs/svg?seed=${username}`;
        return `https://api.dicebear.com/7.x/initials/svg?seed=${username}`;
    };

    if (!currentChannel) {
        return (
            <div className="right-panel">
                <div className="chat-placeholder">
                    Chọn một cuộc trò chuyện để bắt đầu
                </div>
            </div>
        );
    }

    return (
        <div className="right-panel">
            {/* Header */}
            <div className="chat-header">
                <div>
                    <div className="chat-title">#{currentChannel}</div>
                    <div className="chat-subtitle">
                        Đang kết nối với {connectionsCount} peer(s)
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="chat-messages">
                {(!messages || messages.length === 0) ? (
                    <div className="chat-empty">Chưa có tin nhắn trong phòng này.</div>
                ) : (
                    <>
                        <div className="chat-history-label">Lịch sử trò chuyện</div>

                        {messages.map((m, idx) => {
                            const isMe = m.from === meId;
                            return (
                                <div
                                    key={idx}
                                    className={
                                        "message-row" +
                                        (isMe ? " message-row-me" : "")
                                    }
                                >
                                    {!isMe && (
                                        <img
                                            className="message-avatar"
                                            src={getAvatar(m.from)}
                                            alt="avatar"
                                        />
                                    )}

                                    <div
                                        className={
                                            "message-bubble" +
                                            (isMe
                                                ? " message-bubble-me"
                                                : " message-bubble-other")
                                        }
                                    >
                                        {!isMe && (
                                            <div className="message-sender">
                                                {m.from || "unknown"}
                                            </div>
                                        )}

                                        <div>{m.text}</div>

                                        <div className="message-time">
                                            {formatTime(m.ts)}
                                        </div>
                                    </div>

                                    {isMe && (
                                        <img
                                            className="message-avatar"
                                            // src={getAvatar("me")}
                                            src={"/src/assets/1.png"}
                                            alt="avatar"
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </>
                )}
            </div>

            {/* Input */}
            <form className="chat-input-area" onSubmit={handleSubmit}>
                <input
                    className="chat-input"
                    placeholder="Nhập tin nhắn..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                />
                <button type="submit" className="chat-send-btn">
                    Gửi
                </button>
            </form>
        </div>
    );
}

export default ChatWindow;
