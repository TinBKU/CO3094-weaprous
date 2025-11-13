#!/usr/bin/env python3
"""
peer_client.py — Peer client with P2P-first send + tracker-relay fallback.

Behavior:
- Register with tracker via POST /submit-info
- Periodically re-register to refresh TTL
- Fetch peer list from tracker via GET /get-list
- When sending to a peer:
    1) Try cached address and direct TCP connect
    2) If missing or direct connect fails, call tracker /connect-peer (mode=info) to get target address
    3) If still fails, call tracker /send-peer to ask tracker to relay (short-lived)
- Listener expects line-delimited JSON messages
- REPL supports: peers, refresh, send, broadcast, create, join, channels, sendchan, exit
"""
import argparse
import http.client
import json
import logging
import socket
import threading
import time
import urllib.parse
from typing import Dict, Tuple, Optional

# --- Config
REGISTER_RETRIES = 5
FETCH_RETRIES = 3
REREGISTER_INTERVAL = 60
HTTP_TIMEOUT = 5
TCP_CONNECT_TIMEOUT = 4
REREGISTER_BACKOFF = 5  # seconds before retry immediate failures

# --- Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')


class Peer:
    def __init__(self, peer_id: str, bind_host: str, bind_port: int, tracker_url: str):
        self.peer_id = peer_id
        self.bind_host = bind_host
        # host advertised to tracker (use bind_host unless it's 0.0.0.0)
        self.advertise_host = '127.0.0.1' if bind_host == '0.0.0.0' else bind_host
        self.port = int(bind_port)
        self.tracker_url = tracker_url.rstrip('/')
        self.peers: Dict[str, Tuple[str, int]] = {}
        self.lock = threading.Lock()
        self.running = True
        self._listener_sock = None

    # --- helper for tracker URL parsing + HTTP requests
    def _parse_tracker(self):
        parsed = urllib.parse.urlparse(self.tracker_url)
        scheme = parsed.scheme or 'http'
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port or (80 if scheme == 'http' else 443)
        return scheme, host, port

    def _http_request_raw(self, method: str, path: str, body: Optional[bytes] = None, headers: Optional[dict] = None, timeout=HTTP_TIMEOUT):
        scheme, host, port = self._parse_tracker()
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        try:
            if headers is None:
                headers = {}
            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, data
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _http_json(self, method: str, path: str, obj=None, headers=None, timeout=HTTP_TIMEOUT):
        body = None
        if obj is not None:
            body = json.dumps(obj).encode('utf-8')
            if headers is None:
                headers = {}
            headers["Content-Type"] = "application/json"
        status, data = self._http_request_raw(method, path, body=body, headers=headers, timeout=timeout)
        decoded = None
        try:
            decoded = data.decode('utf-8') if data is not None else ''
            parsed = json.loads(decoded) if decoded else {}
        except Exception:
            parsed = {}
        return status, parsed, decoded

    # --- register / fetch peers
    def register_to_tracker(self, retries=REGISTER_RETRIES) -> bool:
        payload = {"peer_id": self.peer_id, "host": self.advertise_host, "port": self.port}
        for attempt in range(1, retries + 1):
            try:
                status, parsed, raw = self._http_json("POST", "/submit-info", obj=payload)
                logging.info("[tracker] register attempt %d -> %s", attempt, status)
                if status in (200, 201):
                    return True
            except Exception as e:
                logging.warning("[tracker] register attempt %d failed: %s", attempt, e)
            time.sleep(1)
        logging.error("[tracker] register failed after retries")
        return False

    def fetch_peers(self, retries=FETCH_RETRIES) -> bool:
        for attempt in range(1, retries + 1):
            try:
                status, parsed, raw = self._http_json("GET", "/get-list")
                if status == 200:
                    newmap = {}
                    for item in parsed.get("peers", []):
                        pid = item.get("peer_id")
                        h = item.get("host")
                        p = int(item.get("port"))
                        if pid:
                            newmap[pid] = (h, p)
                    with self.lock:
                        self.peers = newmap
                    logging.info("[tracker] fetch_peers OK: %s", list(self.peers.keys()))
                    return True
                else:
                    logging.warning("[tracker] get-list returned %s", status)
            except Exception as e:
                logging.warning("[tracker] fetch attempt %d failed: %s", attempt, e)
            time.sleep(1)
        logging.error("[tracker] fetch_peers ultimately failed")
        return False

    # --- re-register loop to refresh TTL (tracker may not have /keepalive)
    def re_register_loop(self):
        while self.running:
            try:
                ok = self.register_to_tracker(retries=1)
                if not ok:
                    logging.info("re-register failed; will retry later")
                # wait with small sleeps to allow quick shutdown
                for _ in range(int(REREGISTER_INTERVAL)):
                    if not self.running:
                        break
                    time.sleep(1)
            except Exception:
                logging.exception("exception in re_register_loop")
                time.sleep(REREGISTER_BACKOFF)

    # --- Listener (accept JSON-per-line)
    def start_listener(self):
        t = threading.Thread(target=self._listener_thread, name="listener", daemon=True)
        t.start()

    def _listener_thread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener_sock = sock
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.bind_host, self.port))
            sock.listen(8)
            sock.settimeout(1.0)
            logging.info("Listening on %s:%d", self.bind_host, self.port)
            while self.running:
                try:
                    conn, addr = sock.accept()
                except socket.timeout:
                    continue
                except Exception:
                    if self.running:
                        logging.exception("accept error")
                    break
                threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()
        except Exception:
            logging.exception("listener error")
            self.running = False
        finally:
            try:
                sock.close()
            except Exception:
                pass
            self._listener_sock = None
            logging.info("listener stopped")

    def _handle_conn(self, conn: socket.socket, addr):
        with conn:
            try:
                f = conn.makefile("rb")
                for raw in f:
                    if not raw:
                        break
                    line = raw.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line.decode('utf-8', errors='ignore'))
                    except Exception:
                        logging.warning("invalid JSON line from %s: %r", addr, line[:200])
                        continue
                    self._process_msg(obj, addr)
            except Exception:
                logging.exception("error handling connection from %s", addr)

    def _process_msg(self, obj: dict, addr):
        try:
            mtype = obj.get("type")
            sender = obj.get("from")
            payload = obj.get("payload")
            if mtype == "message":
                logging.info("[recv] message from %s: %s", sender, payload)
            elif mtype == "channel-msg":
                channel = obj.get("channel")
                logging.info("[recv] channel %s from %s: %s", channel, sender, payload)
            elif mtype == "connect-probe":
                logging.info("[recv] connect-probe from %s", sender)
            else:
                logging.info("[recv] unknown from %s: %s", sender, obj)
        except Exception:
            logging.exception("error processing received message")

    # --- P2P direct send helpers ---
    def _direct_send(self, host: str, port: int, payload_obj: dict, timeout=TCP_CONNECT_TIMEOUT) -> bool:
        try:
            with socket.create_connection((host, int(port)), timeout=timeout) as s:
                s.sendall((json.dumps(payload_obj) + "\n").encode('utf-8'))
            return True
        except Exception as e:
            logging.debug("direct send to %s:%s failed: %s", host, port, e)
            return False

    # --- call tracker to get target info for connect-peer (mode=info) ---
    def ask_tracker_for_target(self, target_peer_id: str) -> Optional[Tuple[str, int]]:
        try:
            payload = {"from": self.peer_id, "to": target_peer_id, "mode": "info"}
            status, parsed, raw = self._http_json("POST", "/connect-peer", obj=payload)
            if status == 200 and parsed.get("target"):
                t = parsed["target"]
                return t.get("host"), int(t.get("port"))
            logging.debug("connect-peer info returned %s / %s", status, parsed)
        except Exception:
            logging.exception("connect-peer request failed")
        return None

    # --- ask tracker to relay message (POST /send-peer) ---
    def send_via_tracker_relay(self, to_peer_id: str, message: str) -> bool:
        try:
            payload = {"to": to_peer_id, "from": self.peer_id, "message": message}
            status, parsed, raw = self._http_json("POST", "/send-peer", obj=payload)
            if status == 200 and parsed.get("ok"):
                logging.info("tracker relayed message to %s", to_peer_id)
                return True
            logging.warning("tracker relay failed: %s %s", status, parsed)
        except Exception:
            logging.exception("tracker relay exception")
        return False

    # --- main send with P2P-first, fallback to tracker ---
    def send_to_peer(self, peer_id: str, payload: str):
        # 1) try cached address first
        with self.lock:
            entry = self.peers.get(peer_id)
        if entry:
            host, port = entry
            logging.info("trying direct send to cached %s -> %s:%s", peer_id, host, port)
            ok = self._direct_send(host, port, {"type": "message", "from": self.peer_id, "to": peer_id, "payload": payload, "ts": time.time()})
            if ok:
                logging.info("sent direct to %s (cached)", peer_id)
                return True
            else:
                logging.info("direct send to cached address failed, will try tracker info")

        # 2) ask tracker for target info and try direct send
        target = self.ask_tracker_for_target(peer_id)
        if target:
            host, port = target
            logging.info("trying direct send to tracker-supplied %s -> %s:%s", peer_id, host, port)
            ok = self._direct_send(host, port, {"type": "message", "from": self.peer_id, "to": peer_id, "payload": payload, "ts": time.time()})
            if ok:
                # update cache
                with self.lock:
                    self.peers[peer_id] = (host, port)
                logging.info("sent direct to %s (tracker info)", peer_id)
                return True
            else:
                logging.info("direct send to tracker-supplied address failed")

        # 3) final fallback: ask tracker to relay via /send-peer
        logging.info("falling back to tracker relay for %s", peer_id)
        ok = self.send_via_tracker_relay(peer_id, payload)
        if ok:
            return True

        logging.error("all send attempts to %s failed", peer_id)
        return False

    # --- broadcast (attempt direct; if a peer unknown, try fetch then relay) ---
    def broadcast(self, payload: str):
        with self.lock:
            peer_ids = [pid for pid in self.peers.keys() if pid != self.peer_id]
        for pid in peer_ids:
            self.send_to_peer(pid, payload)

    # --- channels (create/join/list/sendchan) delegated to tracker endpoints ---
    def create_channel(self, channel_name: str) -> bool:
        try:
            payload = {"channel": channel_name, "owner": self.peer_id}
            status, parsed, raw = self._http_json("POST", "/create-channel", obj=payload)
            logging.info("create_channel: %s %s", status, parsed)
            return status == 201
        except Exception:
            logging.exception("create_channel error")
            return False

    def join_channel(self, channel_name: str) -> bool:
        try:
            payload = {"channel": channel_name, "peer_id": self.peer_id}
            status, parsed, raw = self._http_json("POST", "/join-channel", obj=payload)
            logging.info("join_channel: %s %s", status, parsed)
            return status == 200
        except Exception:
            logging.exception("join_channel error")
            return False

    def list_channels(self):
        try:
            status, parsed, raw = self._http_json("GET", "/list-channels")
            if status == 200:
                return parsed.get("channels", [])
        except Exception:
            logging.exception("list_channels error")
        return []

    def send_channel_msg(self, channel_name: str, message: str):
        chs = self.list_channels()
        members = []
        for ch in chs:
            if ch.get("name") == channel_name:
                members = ch.get("members", [])
                break
        if not members:
            logging.warning("channel %s not found or no members", channel_name)
            return
        msg = {"type": "channel-msg", "from": self.peer_id, "channel": channel_name, "payload": message, "ts": time.time()}
        for m in members:
            if m == self.peer_id:
                continue
            self.send_to_peer(m, msg)   # gửi đúng channel message object

    def stop(self):
        self.running = False
        try:
            if self._listener_sock:
                self._listener_sock.close()
        except Exception:
            pass


# --- simple REPL ---
def repl(peer: Peer):
    print("Commands: peers | refresh | send <peer_id> <message> | broadcast <message>")
    print("          create <channel> | join <channel> | channels | sendchan <channel> <msg> | exit")
    while peer.running:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd:
            continue
        parts = cmd.split(" ", 2)
        cmd0 = parts[0].lower()
        if cmd0 == "peers":
            with peer.lock:
                for pid, (h, p) in peer.peers.items():
                    print(pid, h, p)
        elif cmd0 == "refresh":
            peer.fetch_peers()
        elif cmd0 == "send" and len(parts) >= 3:
            peer_id = parts[1]; msg = parts[2]
            peer.send_to_peer(peer_id, msg)
        elif cmd0 == "broadcast" and len(parts) >= 2:
            peer.broadcast(parts[1])
        elif cmd0 == "create" and len(parts) >= 2:
            peer.create_channel(parts[1])
        elif cmd0 == "join" and len(parts) >= 2:
            peer.join_channel(parts[1])
        elif cmd0 == "channels":
            chs = peer.list_channels()
            for ch in chs:
                print(ch)
        elif cmd0 == "sendchan" and len(parts) >= 3:
            peer.send_channel_msg(parts[1], parts[2])
        elif cmd0 == "exit":
            peer.stop()
            break
        else:
            print("Unknown command")
    print("REPL exiting")


# --- main ---
def main():
    parser = argparse.ArgumentParser(prog="peer")
    parser.add_argument("--peer-id", required=True)
    parser.add_argument("--host", default="0.0.0.0", help="bind host (0.0.0.0 to accept all)")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--tracker", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    p = Peer(args.peer_id, args.host, args.port, args.tracker)
    p.start_listener()

    # register & fetch
    if not p.register_to_tracker():
        logging.warning("initial registration failed; will continue and retry in background")
    p.fetch_peers()

    # re-register background
    t_rr = threading.Thread(target=p.re_register_loop, name="re-register", daemon=True)
    t_rr.start()

    try:
        repl(p)
    finally:
        p.stop()
        logging.info("peer stopped")


if __name__ == "__main__":
    main()
