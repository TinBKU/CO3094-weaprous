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

## 4. Project Structure
/
├── start_proxy.py
├── start_backend.py
├── start_sampleapp.py
├── peer_client_fixed.py
├── daemon/weaprous/
├── static/
└── README.md

## 5. Running Instructions

### Task 1 – HTTP Login System

#### Start Backend
python start_backend.py --server-ip 127.0.0.1 --server-port 9000

#### Start Proxy
python start_proxy.py --server-ip 127.0.0.1 --server-port 8000

Access: http://127.0.0.1:8000/login.html

### Task 2 – Hybrid Chat Application

#### Start Tracker
python start_sampleapp.py --server-ip 127.0.0.1 --server-port 8000

#### Start Peer 1
python peer_client.py --peer-id P1 --host 127.0.0.1 --port 5001

#### Start Peer 2
python peer_client.py --peer-id P2 --host 127.0.0.1 --port 5002

## 6. Example Commands (in peer REPL)
> peers  
> send P2 hello  
> broadcast hi-all  
> create room1  
> join room1  
> sendchan room1 hello-channel  

## 7. Common Errors
- Address already in use → change port.
- Peer unreachable → firewall/NAT.
- TTL expired → auto re-register.

## 8. Conclusion
All requirements for Assignment 1 are completed including:
- Cookie-based HTTP auth
- Reverse proxy + backend separation
- RESTful tracker
- Direct P2P + fallback relay
- Channels + broadcast
