#!/usr/bin/env python3
"""
Solarpunk Mesh Bridge Client

Connect to the mesh bridge over Reticulum and query mesh state
or send commands to ESP32 nodes. Works from any Reticulum peer.

Usage:
  ./bridge_client.py                  # Auto-discover bridge, show state
  ./bridge_client.py <dest_hash>      # Connect to specific bridge
  ./bridge_client.py --cmd <node_ip> <command>  # Send command to node
"""

import json
import sys
import time

import RNS

BRIDGE_NAME = "solarpunk"
BRIDGE_ASPECT = "mesh"


class MeshQuery(RNS.MessageBase):
    MSGTYPE = 0x10
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


class MeshResponse(RNS.MessageBase):
    MSGTYPE = 0x11
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


class MeshCommand(RNS.MessageBase):
    MSGTYPE = 0x12
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


class BridgeClient:
    def __init__(self):
        self.reticulum = RNS.Reticulum()
        self.identity = RNS.Identity()
        self.connected = False
        self.channel = None
        self.response = None

    def discover(self):
        """Find the bridge via Reticulum announces."""
        found = [None]

        def handler(dest_hash, announced_identity, app_data):
            found[0] = dest_hash

        RNS.Transport.register_announce_handler(
            handler, aspect_filter=f"{BRIDGE_NAME}.{BRIDGE_ASPECT}")

        print(f"Searching for mesh bridge...", end="", flush=True)
        timeout = 30
        while found[0] is None and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="", flush=True)
        print()

        return found[0]

    def connect(self, dest_hash_hex=None):
        if dest_hash_hex:
            dest_hash = bytes.fromhex(dest_hash_hex.replace(":", "").replace(" ", ""))
        else:
            dest_hash = self.discover()
            if not dest_hash:
                print("Bridge not found.")
                sys.exit(1)

        if not RNS.Transport.has_path(dest_hash):
            RNS.Transport.request_path(dest_hash)
            time.sleep(2)

        server_id = RNS.Identity.recall(dest_hash)
        dest = RNS.Destination(
            server_id, RNS.Destination.OUT, RNS.Destination.SINGLE,
            BRIDGE_NAME, BRIDGE_ASPECT)

        link = RNS.Link(dest)
        link.set_link_established_callback(self.on_connected)

        timeout = 10
        while not self.connected and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5

        if not self.connected:
            print("Connection timed out.")
            sys.exit(1)

    def on_connected(self, link):
        self.connected = True
        self.channel = link.get_channel()
        self.channel.register_message_type(MeshResponse)
        self.channel.add_message_handler(self.on_response)

    def on_response(self, message):
        if isinstance(message, MeshResponse):
            self.response = message.data
            return True
        return False

    def query_state(self):
        """Request full mesh state."""
        self.response = None
        self.channel.send(MeshQuery(b"state"))

        timeout = 10
        while self.response is None and timeout > 0:
            time.sleep(0.2)
            timeout -= 0.2

        if self.response:
            state = json.loads(self.response.decode())
            print("\n=== Mesh Bridge State ===\n")
            print(f"Bridge: {state.get('bridge', '?')}")

            nodes = state.get("nodes", {})
            print(f"\nESP32 Nodes ({len(nodes)}):")
            for ip, n in nodes.items():
                status = "ONLINE" if n.get("online") else "OFFLINE"
                print(f"  {n['name']} ({ip}) [{status}]")
                print(f"    battery={n['battery']}% solar={n['solar_mv']}mV peers={n['peer_count']} fw={n['version']}")

            peers = state.get("peers", {})
            print(f"\nMesh Peers ({len(peers)}):")
            for name, p in peers.items():
                print(f"  {name}: bat={p.get('battery','?')}% rssi={p.get('rssi','?')} hops={p.get('hops','?')} via={p.get('seen_by','?')}")
        else:
            print("No response from bridge.")

    def send_command(self, node_ip, cmd):
        """Send command to an ESP32 node through the bridge."""
        self.response = None
        payload = json.dumps({"node": node_ip, "cmd": cmd}).encode()
        self.channel.send(MeshCommand(payload))

        timeout = 15
        while self.response is None and timeout > 0:
            time.sleep(0.2)
            timeout -= 0.2

        if self.response:
            result = json.loads(self.response.decode())
            print(f"{result.get('node', '?')}> {result.get('result', '')}")
        else:
            print("No response.")


def main():
    client = BridgeClient()

    dest_hash = None
    if len(sys.argv) > 1 and sys.argv[1] != "--cmd":
        dest_hash = sys.argv[1]

    client.connect(dest_hash)

    if "--cmd" in sys.argv:
        idx = sys.argv.index("--cmd")
        if idx + 2 < len(sys.argv):
            node_ip = sys.argv[idx + 1]
            cmd = " ".join(sys.argv[idx + 2:])
            client.send_command(node_ip, cmd)
        else:
            print("Usage: --cmd <node_ip> <command>")
    else:
        client.query_state()


if __name__ == "__main__":
    main()
