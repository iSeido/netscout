#!/usr/bin/env python3
"""
netscout — Python network scanner for small-office networks.

Usage examples:
  python netscout.py 192.168.1.0/24
  python netscout.py 192.168.1.0/24 --top-ports 50
  python netscout.py 192.168.1.0/24 -p 22,80,443,3389
  python netscout.py 192.168.1.0/24 -p 1-1024 --banners
  python netscout.py 192.168.1.1 -p 1-65535 -o results.json
  python netscout.py 192.168.1.0/24 --discover-only
"""

import argparse
import sys
import time

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn

from scanner.discovery import discover_hosts
from scanner.port_scanner import scan_network, parse_ports
from scanner.reporter import print_results, print_discovery_results, export_json, export_csv
from scanner.service_info import TOP_PORTS

console = Console()

BANNER = """
[bold cyan]
 ███╗   ██╗███████╗████████╗███████╗ ██████╗ ██████╗ ██╗   ██╗████████╗
 ████╗  ██║██╔════╝╚══██╔══╝██╔════╝██╔════╝██╔═══██╗██║   ██║╚══██╔══╝
 ██╔██╗ ██║█████╗     ██║   ███████╗██║     ██║   ██║██║   ██║   ██║
 ██║╚██╗██║██╔══╝     ██║   ╚════██║██║     ██║   ██║██║   ██║   ██║
 ██║ ╚████║███████╗   ██║   ███████║╚██████╗╚██████╔╝╚██████╔╝   ██║
 ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝
[/bold cyan]
[dim]Network Scout — identify devices and open ports on your local network[/dim]
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netscout",
        description="Scan local networks for connected devices and open ports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python netscout.py 192.168.1.0/24                  discover hosts + scan top 20 ports
  python netscout.py 192.168.1.0/24 --top-ports 100  scan top 100 common ports
  python netscout.py 192.168.1.0/24 -p 22,80,443     scan specific ports
  python netscout.py 192.168.1.0/24 -p 1-1024        scan port range
  python netscout.py 192.168.1.1 --banners            grab service banners
  python netscout.py 192.168.1.0/24 --discover-only   ping sweep only
  python netscout.py 192.168.1.0/24 -o out.json       export results to JSON
  python netscout.py 192.168.1.0/24 -o out.csv        export results to CSV
        """,
    )
    parser.add_argument("target", help="IP address or CIDR range (e.g. 192.168.1.0/24)")

    port_group = parser.add_mutually_exclusive_group()
    port_group.add_argument(
        "-p", "--ports",
        metavar="PORTS",
        help="ports to scan: '80', '22,80,443', '1-1024', or mixed '22,80,443-450'",
    )
    port_group.add_argument(
        "--top-ports",
        type=int,
        choices=[20, 50, 100],
        default=20,
        metavar="N",
        help="scan top N common ports (20, 50, or 100) [default: 20]",
    )

    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="only run host discovery (ping sweep), skip port scanning",
    )
    parser.add_argument(
        "--banners",
        action="store_true",
        help="attempt to grab service banners from open ports",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        metavar="SEC",
        help="socket/ping timeout in seconds [default: 1.0]",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=100,
        metavar="N",
        help="max concurrent port-scan threads per host [default: 100]",
    )
    parser.add_argument(
        "--ping-threads",
        type=int,
        default=50,
        metavar="N",
        help="max concurrent ping threads for discovery [default: 50]",
    )
    parser.add_argument(
        "--host-threads",
        type=int,
        default=10,
        metavar="N",
        help="max concurrent host-scan threads [default: 10]",
    )
    parser.add_argument(
        "--no-ping",
        action="store_true",
        help="skip host discovery — scan target directly (useful for single IPs)",
    )
    parser.add_argument(
        "--show-closed",
        action="store_true",
        help="also display closed ports in output",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="export results to file (.json or .csv)",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="suppress the ASCII art banner",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.no_banner:
        console.print(BANNER)

    # Resolve port list
    if args.ports:
        try:
            ports = parse_ports(args.ports)
        except ValueError as e:
            console.print(f"[red]Invalid port spec:[/red] {e}")
            return 1
    else:
        ports = TOP_PORTS[args.top_ports]

    console.print(f"[bold]Target:[/bold]  {args.target}")
    console.print(f"[bold]Ports:[/bold]   {len(ports)} selected")
    console.print()

    # Phase 1 — Host Discovery
    if args.no_ping:
        live_hosts = [args.target]
        console.print(f"[dim]Skipping discovery — scanning {args.target} directly.[/dim]\n")
    else:
        console.print("[bold]Phase 1 — Host Discovery[/bold]")
        t0 = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Pinging hosts...", total=None)

            def ping_progress(done, total):
                progress.update(task, completed=done, total=total)

            live_hosts = discover_hosts(
                args.target,
                max_workers=args.ping_threads,
                timeout_ms=int(args.timeout * 1000),
                progress_callback=ping_progress,
            )

        console.print(f"Discovery complete in {time.time() - t0:.1f}s\n")
        print_discovery_results(live_hosts)

    if args.discover_only or not live_hosts:
        return 0

    # Phase 2 — Port Scanning
    console.print("[bold]Phase 2 — Port Scanning[/bold]")
    t0 = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning hosts...", total=None)

        def scan_progress(done, total):
            progress.update(task, completed=done, total=total)

        results = scan_network(
            live_hosts,
            ports,
            port_workers=args.threads,
            host_workers=args.host_threads,
            timeout=args.timeout,
            grab_banners=args.banners,
            progress_callback=scan_progress,
        )

    console.print(f"Scan complete in {time.time() - t0:.1f}s\n")
    print_results(results, show_closed=args.show_closed)

    if args.output:
        if args.output.endswith(".csv"):
            export_csv(results, args.output)
        else:
            export_json(results, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
