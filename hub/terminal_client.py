#!/usr/bin/env python3
"""
Solarpunk Reticulum Terminal Client

Connects to the Pi's terminal server over Reticulum and provides
an interactive shell session. Run this from any machine on the network.
"""

import os
import sys
import tty
import termios
import select
import time
import threading

import RNS

APP_NAME = "solarpunk"
ASPECT = "terminal"


class TerminalClient:
    def __init__(self, dest_hash=None):
        self.reticulum = RNS.Reticulum()
        self.identity = RNS.Identity()
        self.link = None
        self.channel = None
        self.connected = False
        self.dest_hash = dest_hash

    def connect(self, dest_hash_hex=None):
        if dest_hash_hex:
            dest_hash = bytes.fromhex(dest_hash_hex.replace(":", "").replace(" ", ""))
        elif self.dest_hash:
            dest_hash = self.dest_hash
        else:
            print("Searching for terminal servers...")
            dest_hash = self._discover()
            if not dest_hash:
                print("No terminal server found. Make sure the server is running.")
                sys.exit(1)

        print(f"Connecting to {RNS.prettyhexrep(dest_hash)}...")

        # Resolve path to destination
        if not RNS.Transport.has_path(dest_hash):
            RNS.Transport.request_path(dest_hash)
            print("Requesting path...", end="", flush=True)
            timeout = 15
            while not RNS.Transport.has_path(dest_hash) and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
                print(".", end="", flush=True)
            print()
            if not RNS.Transport.has_path(dest_hash):
                print("Could not find path to server.")
                sys.exit(1)

        server_identity = RNS.Identity.recall(dest_hash)
        dest = RNS.Destination(
            server_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME,
            ASPECT,
        )

        self.link = RNS.Link(dest)
        self.link.set_link_established_callback(self.on_connected)
        self.link.set_link_closed_callback(self.on_disconnected)

        print("Waiting for link...", end="", flush=True)
        timeout = 15
        while not self.connected and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5
            print(".", end="", flush=True)
        print()

        if not self.connected:
            print("Connection timed out.")
            sys.exit(1)

    def _discover(self):
        """Listen for announces from terminal servers."""
        found = [None]

        def announce_handler(dest_hash, announced_identity, app_data):
            RNS.log(f"Found server: {RNS.prettyhexrep(dest_hash)}", RNS.LOG_INFO)
            found[0] = dest_hash

        RNS.Transport.register_announce_handler(
            announce_handler,
            aspect_filter=f"{APP_NAME}.{ASPECT}",
        )

        # Wait up to 30 seconds for an announce
        timeout = 30
        print(f"Listening for announces ({timeout}s)...", end="", flush=True)
        while found[0] is None and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="", flush=True)
        print()

        return found[0]

    def on_connected(self, link):
        self.connected = True
        self.channel = link.get_channel()
        self.channel.register_message_type(TerminalOutput)
        self.channel.add_message_handler(self.on_output)
        print("\r\nConnected! You have a shell on the Pi.\r\n")
        print("Press Ctrl+] to disconnect.\r\n")

    def on_disconnected(self, link):
        self.connected = False
        print("\r\nDisconnected.\r\n")

    def on_output(self, message):
        """Receive terminal output and write to local stdout."""
        if not isinstance(message, TerminalOutput):
            return False
        os.write(sys.stdout.fileno(), message.data)
        return True

    def run_interactive(self):
        """Main input loop - raw terminal mode."""
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while self.connected:
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    char = os.read(sys.stdin.fileno(), 1024)
                    # Ctrl+] to disconnect
                    if b'\x1d' in char:
                        break
                    if self.channel:
                        msg = TerminalInput(char)
                        self.channel.send(msg)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        if self.link:
            self.link.teardown()
        print("Session ended.")


# Same message types as server
class TerminalInput(RNS.MessageBase):
    MSGTYPE = 0x01

    def __init__(self, data=None):
        self.data = data

    def pack(self):
        return self.data

    def unpack(self, raw):
        self.data = raw


class TerminalOutput(RNS.MessageBase):
    MSGTYPE = 0x02

    def __init__(self, data=None):
        self.data = data

    def pack(self):
        return self.data

    def unpack(self, raw):
        self.data = raw


def main():
    dest_hash = None
    if len(sys.argv) > 1:
        dest_hash = sys.argv[1]

    client = TerminalClient()
    client.connect(dest_hash)
    client.run_interactive()


if __name__ == "__main__":
    main()
