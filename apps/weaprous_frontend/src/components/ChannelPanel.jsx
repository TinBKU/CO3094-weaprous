// src/components/ChannelPanel.jsx
import React, { useState } from "react";

function ChannelPanel({
    currentChannel,
    joinedChannels,
    onSelectChannel,
    onCreateChannel,
    unreadByChannel = {}   // <-- App pass xuống
}) {
    const [creating, setCreating] = useState(false);
    const [newRoom, setNewRoom] = useState("");

    // LỌC BỎ "__meta__"
    const visibleChannels = [...joinedChannels].filter(
        (ch) => ch !== "__meta__"
    );

    return (
        <>
            <div className="channels-header">
                <span>Kênh</span>
                <button onClick={() => setCreating(!creating)}>+ Tạo</button>
            </div>

            {creating && (
                <div style={{ padding: "6px 12px" }}>
                    <input
                        placeholder="Tên kênh..."
                        value={newRoom}
                        onChange={(e) => setNewRoom(e.target.value)}
                        style={{
                            width: "100%",
                            padding: 6,
                            borderRadius: 6,
                            border: "1px solid #ddd",
                        }}
                    />
                    <button
                        style={{
                            marginTop: 6,
                            width: "100%",
                            background: "#2563eb",
                            color: "#fff",
                            padding: 6,
                            borderRadius: 6,
                            border: 0,
                            cursor: "pointer",
                        }}
                        onClick={() => {
                            if (newRoom.trim()) {
                                onCreateChannel(newRoom.trim());
                                setNewRoom("");
                                setCreating(false);
                            }
                        }}
                    >
                        Tạo phòng
                    </button>
                </div>
            )}

            <div className="channel-list">
                {visibleChannels.map((ch) => {
                    const active = ch === currentChannel;
                    const unread = unreadByChannel[ch] || 0;   // <-- chỉ đọc từ App

                    return (
                        <div
                            key={ch}
                            className={`channel-item ${active ? "channel-item-active" : ""
                                }`}
                            onClick={() => onSelectChannel(ch)}
                        >
                            <div className="channel-avatar">
                                {ch[0]?.toUpperCase() || "#"}
                            </div>
                            <div className="channel-main">
                                <div className="channel-name">{ch}</div>
                                <div className="channel-lastmsg">
                                    Nhấp để xem tin nhắn
                                </div>
                            </div>
                            {unread > 0 && (
                                <div className="channel-unread-badge">
                                    {unread > 9 ? "9+" : unread}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </>
    );
}

export default ChannelPanel;
