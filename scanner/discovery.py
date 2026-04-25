"""Host discovery via ICMP ping sweep."""

import platform
import subprocess
import ipaddress
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def _ping(host: str, timeout_ms: int = 1000) -> bool:
    """Return True if host responds to ping."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, round(timeout_ms / 1000))), host]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_ms / 1000 + 1,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def discover_hosts(
    network: str,
    max_workers: int = 50,
    timeout_ms: int = 1000,
    progress_callback=None,
) -> list[str]:
    """
    Ping-sweep a CIDR network and return list of live host IPs.

    Args:
        network: CIDR notation e.g. '192.168.1.0/24' or single IP '192.168.1.1'
        max_workers: concurrent ping threads
        timeout_ms: ping timeout in milliseconds
        progress_callback: optional callable(completed, total) for progress updates
    """
    try:
        net = ipaddress.ip_network(network, strict=False)
        hosts = list(net.hosts()) if net.num_addresses > 1 else [net.network_address]
    except ValueError as e:
        raise ValueError(f"Invalid network/IP: {network!r} — {e}") from e

    live: list[str] = []
    total = len(hosts)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_ping, str(h), timeout_ms): str(h) for h in hosts}
        for future in as_completed(futures):
            ip = futures[future]
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
            try:
                if future.result():
                    live.append(ip)
            except Exception as e:
                print(f"[discovery] ping {ip}: {e}", file=sys.stderr)

    live.sort(key=lambda ip: tuple(int(p) for p in ip.split(".")))
    return live
