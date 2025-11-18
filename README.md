# README — Assignment 1
## HTTP Server with Cookie-based Authentication & Hybrid P2P Chat Application
### CO3093/CO3094 – Computer Networks – HCMUT

## 1. Members
| STT | Full Name | Student ID | Role |
|-----|-----------|------------|-------|
| 1 | [Giang Phi Vân] | [2313867] | HTTP server with cookie session |
| 2 | [Tôn Trọng Tín] | [2033338] | Hybrid chat application |


## 2. Introduction
Assignment 1 consists of two independent networking systems:

### Task 1 – HTTP Server + Cookie-based Authentication
- Build a login system using WeApRous.
- POST /login verifies credentials.
- Successful login sets cookie `auth=true`.
- Requests to `/` or `/hello` must check cookie.
- If cookie missing → 401 Unauthorized.

### Task 2 – Hybrid Chat System (Client–Server + P2P)
- Tracker RESTful server stores peer list.
- Peer clients run TCP servers.
- Support:
  - Direct P2P messaging
  - Tracker fallback relay
  - Broadcast
  - Channels (create, join, list, send)

## 3. System Architecture
Task 1:
Browser → start_proxy.py → start_backend.py → Response

Task 2:
Peer A ↔ Peer B (TCP)
Peer → Tracker (REST)

## 4. Running Instructions

### Task 1 – HTTP Login System
#### Start Backend
python start_backend.py --server-ip 127.0.0.1 --server-port 9000

#### Start Proxy
python start_proxy.py --server-ip 127.0.0.1 --server-port 8000

Access: http://127.0.0.1:8000/login.html

### Task 2 – Hybrid Chat Application
#### 1.Start Frontend
vào apps\weaprous_frontend
mở cmd chạy lệnh npm run dev
yêu cầu cài nodejs và chạy lệnh npm install

#### 2.Start Backend 
python start_sampleapp.py 

#### 3.Start Tracker
python tracker_server.py 

#### 4.Start Peer 1
python peer_client.py --id admin --host 127.0.0.1 --port 10001 --ws-port 7000 --auth-mode soft


#### 5.Start Peer 2
python peer_client.py --id user --host 127.0.0.1 --port 10002 --ws-port 7002 --auth-mode soft


##Common Errors
- Address already in use → change port.
- Peer unreachable → firewall/NAT.
- TTL expired → auto re-register.

## Conclusion
All requirements for Assignment 1 are completed including:
- Cookie-based HTTP auth
- RESTful tracker
- Direct P2P + fallback relay
- Channels + broadcast

## ⚙️ Python Version Requirement
Project tested and verified using:
Ensure your environment uses:
```bash
python --version
# Python 3.14.0 (recommended)