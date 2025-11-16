// src/pages/LoginPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const LOGIN_URL = "http://127.0.0.1:9000/login";

function LoginPage() {
    const [username, setUsername] = useState("admin");
    const [password, setPassword] = useState("password");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        try {
            setLoading(true);
            const body = new URLSearchParams({
                username: username.trim(),
                password: password.trim(),
            }).toString();

            const resp = await fetch(LOGIN_URL, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body,
                credentials: "include", // nhận cookie session
            });

            const data = await resp.json().catch(() => ({}));

            if (resp.ok && data.ok) {
                // Lưu thông tin auth đơn giản trong localStorage
                localStorage.setItem(
                    "chatAuth",
                    JSON.stringify({
                        user: data.user,
                        peerId: data.peer_id,
                        wsPort: data.ws_port,
                    })
                );
                navigate("/chat");
            } else if (resp.status === 401) {
                setError("Sai username/password (demo: admin / password).");
            } else {
                setError(
                    `Lỗi đăng nhập: HTTP ${resp.status} - ${data.error || data.msg || "Unknown"
                    }`
                );
            }
        } catch (err) {
            console.error("Login error:", err);
            setError("Không kết nối được tới server đăng nhập (9000).");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-wrapper">
            <div className="login-card">
                <div className="login-title">Đăng nhập hệ thống chat</div>
                <div className="login-subtitle">
                    Vui lòng đăng nhập để sử dụng dịch vụ chat P2P.
                </div>

                <form className="login-form" onSubmit={handleSubmit}>
                    <label className="login-label">
                        Tên đăng nhập
                        <input
                            className="login-input"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="vd: admin"
                        />
                    </label>
                    <label className="login-label">
                        Mật khẩu
                        <input
                            type="password"
                            className="login-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="vd: password"
                        />
                    </label>

                    {error && <div className="login-error" style={{ color: "red" }}>{error}</div>}

                    <button type="submit" className="login-button" disabled={loading}>
                        {loading ? "Đang kiểm tra..." : "Đăng nhập"}
                    </button>
                </form>

                <div className="login-footer">
                    Demo: <code>admin / password</code>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
