#!/usr/bin/env python3
"""
Solarpunk Reticulum Terminal Server

Runs on the Pi as a Reticulum destination that provides shell access.
Any Reticulum peer can connect and get an interactive terminal session.
"""

import os
import sys
import pty
import select
import signal
import struct
import threading
import time

import RNS

APP_NAME = "solarpunk"
ASPECT = "terminal"

class TerminalServer:
    def __init__(self):
        self.reticulum = RNS.Reticulum()
        self.identity = self._load_or_create_identity()

        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            APP_NAME,
            ASPECT,
        )
        self.destination.set_link_established_callback(self.on_link)
        self.destination.announce()

        self.sessions = {}
        RNS.log(f"Terminal server running", RNS.LOG_NOTICE)
        RNS.log(f"Identity hash: {self.identity.hexhash}", RNS.LOG_NOTICE)
        RNS.log(f"Destination hash: {RNS.prettyhexrep(self.destination.hash)}", RNS.LOG_NOTICE)

    def _load_or_create_identity(self):
        id_path = os.path.expanduser("~/.reticulum/terminal_server_identity")
        if os.path.exists(id_path):
            identity = RNS.Identity.from_file(id_path)
            RNS.log("Loaded existing identity", RNS.LOG_INFO)
        else:
            identity = RNS.Identity()
            identity.to_file(id_path)
            RNS.log("Created new identity", RNS.LOG_INFO)
        return identity

    def on_link(self, link):
        link.set_remote_identified_callback(self.on_identified)
        link.set_link_closed_callback(self.on_link_closed)
        RNS.log(f"Link established from {RNS.prettyhexrep(link.hash)}", RNS.LOG_NOTICE)
        # Start session immediately (no auth for now, encrypted by default)
        self._start_session(link)

    def on_identified(self, link, identity):
        RNS.log(f"Remote identified: {identity.hexhash}", RNS.LOG_INFO)

    def on_link_closed(self, link):
        RNS.log(f"Link closed: {RNS.prettyhexrep(link.hash)}", RNS.LOG_NOTICE)
        session = self.sessions.pop(link.hash, None)
        if session:
            session.stop()

    def _start_session(self, link):
        session = ShellSession(link)
        self.sessions[link.hash] = session
        session.start()

    def run(self):
        RNS.log("Waiting for connections...", RNS.LOG_NOTICE)
        # Re-announce periodically so peers can discover us
        while True:
            time.sleep(300)
            self.destination.announce()
            RNS.log(f"Re-announced. Active sessions: {len(self.sessions)}", RNS.LOG_INFO)


class ShellSession:
    """Manages a PTY shell session bridged over a Reticulum link."""

    CHUNK_SIZE = RNS.Link.MDU  # Max data per packet

    def __init__(self, link):
        self.link = link
        self.channel = link.get_channel()
        self.running = False
        self.master_fd = None
        self.pid = None
        self.reader_thread = None

        # Register message handler on the channel
        self.channel.register_message_type(TerminalInput)
        self.channel.add_message_handler(self.on_input)

    def start(self):
        self.pid, self.master_fd = pty.fork()
        if self.pid == 0:
            # Child process - exec shell
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLUMNS"] = "80"
            os.environ["LINES"] = "24"
            os.execvp("/bin/bash", ["/bin/bash", "--login"])
        else:
            # Parent - read PTY output and send to link
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_pty, daemon=True)
            self.reader_thread.start()
            RNS.log(f"Shell session started (PID {self.pid})", RNS.LOG_INFO)

    def on_input(self, message):
        """Handle incoming terminal input from remote client."""
        if not isinstance(message, TerminalInput):
            return False
        if self.master_fd and self.running:
            try:
                os.write(self.master_fd, message.data)
            except OSError:
                self.stop()
        return True

    def _read_pty(self):
        """Read PTY output and send to remote client via channel."""
        while self.running:
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    data = os.read(self.master_fd, self.CHUNK_SIZE)
                    if data:
                        msg = TerminalOutput(data)
                        self.channel.send(msg)
                    else:
                        break
            except OSError:
                break
        self.stop()

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0)
            except (OSError, ChildProcessError):
                pass
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        RNS.log("Shell session ended", RNS.LOG_INFO)


# Message types for the Reticulum channel
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
    try:
        server = TerminalServer()
        server.run()
    except KeyboardInterrupt:
        RNS.log("Server shutting down", RNS.LOG_NOTICE)
        sys.exit(0)

if __name__ == "__main__":
    main()
