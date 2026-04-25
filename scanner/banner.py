"""Service banner grabbing via raw TCP socket."""

import socket

_HTTP_PORTS = {80, 8080, 8000}
_TLS_PORTS = {443, 8443}
_HTTP_HEAD = b"HEAD / HTTP/1.0\r\nHost: "


def grab_banner(host: str, port: int, timeout: float = 2.0) -> str | None:
    """
    Connect to host:port and read any banner the service sends on connect.
    Returns decoded string or None if nothing received / connection fails.
    """
    if port in _TLS_PORTS:
        return "TLS"

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            if port in _HTTP_PORTS:
                sock.sendall(_HTTP_HEAD + host.encode() + b"\r\n\r\n")
                try:
                    data = sock.recv(1024)
                except socket.timeout:
                    return None
            else:
                try:
                    data = sock.recv(1024)
                except socket.timeout:
                    sock.sendall(_HTTP_HEAD + host.encode() + b"\r\n\r\n")
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
