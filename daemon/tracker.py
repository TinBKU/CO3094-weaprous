import threading
import time

class Tracker:
    def __init__(self):
        self._lock = threading.Lock()
        # peer_id -> {"peer_id":..., "ip":..., "port":..., "last_seen": epoch}
        self.peers = {}

    def register(self, peer_id, ip, port):
        with self._lock:
            self.peers[peer_id] = {"peer_id": peer_id, "ip": ip, "port": port, "last_seen": time.time()}

    def unregister(self, peer_id):
        with self._lock:
            if peer_id in self.peers:
                del self.peers[peer_id]

    def list_peers(self):
        with self._lock:
            # Return list copy
            return [dict(v) for v in self.peers.values()]