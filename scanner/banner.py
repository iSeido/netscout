"""Service banner grabbing via raw TCP socket."""

import socket


def grab_banner(host: str, port: int, timeout: float = 2.0) -> str | None:
    """
    Connect to host:port and read any banner the service sends on connect.
    Returns decoded string or None if nothing received / connection fails.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            try:
                data = sock.recv(1024)
            except socket.timeout:
                # Service didn't speak first — try HTTP probe
                sock.sendall(b"HEAD / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
                try:
                    data = sock.recv(1024)
                except socket.timeout:
                    return None
            if data:
                banner = data.decode("utf-8", errors="replace").strip()
                return banner.splitlines()[0][:120] if banner else None
    except (OSError, socket.error):
        return None
    return None
