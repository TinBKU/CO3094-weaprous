// src/components/SidebarPeers.jsx
import React from "react";

function SidebarPeers({
    peers,
    meId,
    wsStatus,
    onConnectPeer,
    onRefreshPeers,
    onAutoConnect,
    onStartChat
}) {
    const peerEntries = Object.entries(peers || {});

    return (
        <>
            {/* Caption + actions */}
            <div className="section-caption">
                <span>Peers ({peerEntries.length})</span>
                <div style={{ display: "flex", gap: 8 }}>
                    {/* {onAutoConnect && (
                        <button type="button" onClick={onAutoConnect}>
                            Auto-connect
                        </button>
                    )} */}
                    <button type="button" onClick={onRefreshPeers}>
                        Refresh
                    </button>
                </div>
            </div>

            {/* List peers */}
            <div className="peers-list">
                {peerEntries.length === 0 ? (
                    <div className="peers-empty">
                        Chưa có peer nào từ tracker.
                    </div>
                ) : (
                    peerEntries.map(([peerId, info]) => (
                        <div
                            key={peerId}
                            className="peer-item"
                            onClick={() => onStartChat && onStartChat(peerId)}
                        >
                            <div>
                                <div className="peer-name">
                                    {peerId}
                                    {peerId === meId && " (me)"}
                                </div>
                                <div className="peer-ip">
                                    {info.ip}:{info.port}
                                </div>
                            </div>
                            <div className="peer-status">
                                WS: {wsStatus}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </>
    );
}

export default SidebarPeers;
