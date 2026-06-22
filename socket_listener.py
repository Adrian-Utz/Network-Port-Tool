import socket
import threading
from typing import Callable

# This module provides a simple socket listener that can be used to receive messages over TCP.
# The SocketListener class encapsulates the functionality of a TCP server that listens for incoming connections 
# and processes messages using a provided callback function. It supports starting and stopping the listener, 
# handling multiple clients concurrently, and managing active listeners through a registry.

class SocketListener:
    def __init__(self, host: str, port: int, on_message: Callable[[str], None], backlog: int = 5) -> None:
        self.host = host
        self.port = port
        self.on_message = on_message
        self.backlog = backlog
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(backlog)
        self.server_socket.settimeout(1.0)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    #Start the Listener
    def start(self) -> "SocketListener":
        self._thread.start()
        return self

    #Stop the Listener
    def stop(self) -> None:
        self._stop_event.set()
        try:
            self.server_socket.close()
        except OSError:
            pass


    def _run(self) -> None:
        #Here we accept incoming connections and create a new thread to handle each client
        while not self._stop_event.is_set():
            try:
                client_socket, _ = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
            client_thread.start()


    def _handle_client(self, client_socket: socket.socket) -> None:
        client_socket.settimeout(1.0)
        #Recieve data from the client and call the on_message callback for each message
        try:
            while not self._stop_event.is_set():
                try:
                    data = client_socket.recv(4096)
                except socket.timeout:
                    continue
                except OSError:
                    break

                if not data:
                    break
                #Decode the received data and call the on_message callback
                message = data.decode("utf-8", errors="replace").strip()
                if message:
                    self.on_message(message)
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

"""Module-level convenience helpers and registry for active socket listeners."""

# Registry of active listeners keyed by (host, port)
_active_listeners: dict[tuple[str, int], SocketListener] = {}


def start_socket_listener(host: str, port: int, on_message: Callable[[str], None]) -> SocketListener:
    """Start and register a background socket listener and return its controller.

    If a listener for the same (host, port) already exists, the existing listener
    is returned.
    """
    key = (host, port)
    if key in _active_listeners:
        return _active_listeners[key]

    listener = SocketListener(host, port, on_message)
    try:
        listener.start()
    except Exception:
        # If starting the thread raises for any reason, ensure no half-registered state
        try:
            listener.stop()
        except Exception:
            pass
        raise

    _active_listeners[key] = listener
    return listener


def stop_socket_listener(host: str, port: int) -> None:
    """Stop and unregister the listener for the given host/port if present."""
    key = (host, port)
    listener = _active_listeners.get(key)
    if not listener:
        return
    try:
        listener.stop()
    finally:
        _active_listeners.pop(key, None)


def list_active_ports() -> list[tuple[str, int]]:
    """Return a list of (host, port) tuples for currently active listeners."""
    return list(_active_listeners.keys())


def get_listener(host: str, port: int) -> SocketListener | None:
    """Return the listener instance for the given host/port or None."""
    return _active_listeners.get((host, port))


def send_message(host: str, port: int, message: str, timeout: float = 3.0) -> None:
    """Send a UTF-8 message to a specific host and port over TCP.

    The message is sent as a single data payload and the socket is closed once
    transmission is complete.
    """
    if not message:
        raise ValueError("Message must not be empty")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.settimeout(timeout)
        client_socket.connect((host, port))
        client_socket.sendall(message.encode("utf-8"))