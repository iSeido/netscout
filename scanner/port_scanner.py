"""Threaded TCP port scanner."""

import errno
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from scanner.service_info import get_service_name
from scanner.banner import grab_banner

_REFUSED: set[int] = {errno.ECONNREFUSED}
_FILTERED: set[int] = set()
for _name in ("ETIMEDOUT", "EHOSTUNREACH", "ENETUNREACH"):
    if (_v := getattr(errno, _name, None)) is not None:
        _FILTERED.add(_v)
for _name in ("WSAECONNREFUSED",):
    if (_v := getattr(errno, _name, None)) is not None:
        _REFUSED.add(_v)
for _name in ("WSAETIMEDOUT", "WSAEHOSTUNREACH", "WSAENETUNREACH"):
    if (_v := getattr(errno, _name, None)) is not None:
        _FILTERED.add(_v)


@dataclass
class PortResult:
    port: int
    state: str          # "open" | "closed" | "filtered"
    service: str
    banner: str | None = field(default=None)


@dataclass
class HostResult:
    ip: str
    ports: list[PortResult] = field(default_factory=list)

    @property
    def open_ports(self) -> list[PortResult]:
        return [p for p in self.ports if p.state == "open"]


def _scan_port(host: str, port: int, timeout: float, grab: bool) -> PortResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        err = sock.connect_ex((host, port))
        if err == 0:
            state = "open"
        elif err in _REFUSED:
            state = "closed"
        elif err in _FILTERED:
            state = "filtered"
        else:
            state = "closed"
    except socket.timeout:
        state = "filtered"
    except OSError:
        state = "filtered"
    finally:
        sock.close()

    banner = None
    if state == "open" and grab:
        banner = grab_banner(host, port, timeout=timeout)

    return PortResult(
        port=port,
        state=state,
        service=get_service_name(port),
        banner=banner,
    )


def scan_host(
    ip: str,
    ports: list[int],
    max_workers: int = 100,
    timeout: float = 1.0,
    grab_banners: bool = False,
    progress_callback=None,
) -> HostResult:
    """Scan all given ports on a single host, return HostResult."""
    result = HostResult(ip=ip)
    total = len(ports)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_scan_port, ip, port, timeout, grab_banners): port
            for port in ports
        }
        for future in as_completed(futures):
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
            try:
                result.ports.append(future.result())
            except Exception as e:
                print(f"[port_scanner] port {futures[future]} on {ip}: {e}", file=sys.stderr)

    result.ports.sort(key=lambda p: p.port)
    return result


def scan_network(
    hosts: list[str],
    ports: list[int],
    port_workers: int = 100,
    host_workers: int = 10,
    timeout: float = 1.0,
    grab_banners: bool = False,
    progress_callback=None,
) -> list[HostResult]:
    """Scan ports on multiple hosts concurrently, return list of HostResult."""
    results: list[HostResult] = []
    total = len(hosts)
    completed = 0

    with ThreadPoolExecutor(max_workers=host_workers) as pool:
        futures = {
            pool.submit(scan_host, ip, ports, port_workers, timeout, grab_banners): ip
            for ip in hosts
        }
        for future in as_completed(futures):
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
            try:
                results.append(future.result())
            except Exception as e:
                print(f"[port_scanner] host {futures[future]}: {e}", file=sys.stderr)

    results.sort(key=lambda r: tuple(int(p) for p in r.ip.split(".")))
    return results


def parse_ports(port_spec: str) -> list[int]:
    """
    Parse port spec string into sorted list of ints.

    Accepted: "80", "80,443", "1-1024", "22,80,443-450"
    """
    ports: set[int] = set()
    for token in port_spec.split(","):
        token = token.strip()
        if "-" in token:
            start_s, _, end_s = token.partition("-")
            start, end = int(start_s), int(end_s)
            if start > end:
                raise ValueError(f"Invalid range '{token}': start {start} > end {end}")
            if start < 1 or end > 65535:
                raise ValueError(f"Invalid range '{token}': ports must be 1–65535")
            ports.update(range(start, end + 1))
        else:
            ports.add(int(token))
    return sorted(p for p in ports if 1 <= p <= 65535)
