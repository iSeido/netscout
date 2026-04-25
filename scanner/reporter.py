"""Output formatting: rich terminal table, JSON, and CSV export."""

import csv
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

from scanner.port_scanner import HostResult

console = Console()


def _state_style(state: str) -> Text:
    styles = {"open": "bold green", "closed": "dim", "filtered": "yellow"}
    return Text(state, style=styles.get(state, ""))


def print_results(results: list[HostResult], show_closed: bool = False) -> None:
    """Print scan results as rich tables, one per live host."""
    open_hosts = [r for r in results if r.open_ports]

    if not open_hosts:
        console.print("\n[yellow]No open ports found on any host.[/yellow]")
        return

    for host in open_hosts:
        table = Table(
            title=f"[bold cyan]{host.ip}[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            min_width=60,
        )
        table.add_column("Port", style="cyan", width=8)
        table.add_column("State", width=10)
        table.add_column("Service", style="green", width=18)
        table.add_column("Banner", style="dim", overflow="fold")

        ports_to_show = host.ports if show_closed else host.open_ports
        for p in ports_to_show:
            table.add_row(
                str(p.port),
                _state_style(p.state),
                p.service,
                p.banner or "",
            )

        console.print(table)

    total_open = sum(len(h.open_ports) for h in results)
    console.print(
        f"\n[bold]Summary:[/bold] {len(open_hosts)} host(s) with open ports, "
        f"{total_open} open port(s) total.\n"
    )


def print_discovery_results(live_hosts: list[str]) -> None:
    """Print discovered hosts list."""
    if not live_hosts:
        console.print("[yellow]No hosts responded to ping.[/yellow]")
        return

    table = Table(
        title="[bold cyan]Live Hosts[/bold cyan]",
        box=box.SIMPLE_HEAVY,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("IP Address", style="cyan")

    for i, ip in enumerate(live_hosts, 1):
        table.add_row(str(i), ip)

    console.print(table)
    console.print(f"[bold]{len(live_hosts)} host(s) found.[/bold]\n")


def export_json(results: list[HostResult], path: str) -> None:
    """Export results to JSON file."""
    data = [
        {
            "ip": host.ip,
            "open_ports": [
                {"port": p.port, "service": p.service, "banner": p.banner}
                for p in host.open_ports
            ],
        }
        for host in results
        if host.open_ports
    ]
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]JSON saved → {path}[/green]")


def export_csv(results: list[HostResult], path: str) -> None:
    """Export results to CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ip", "port", "service", "banner"])
        for host in results:
            for p in host.open_ports:
                writer.writerow([host.ip, p.port, p.service, p.banner or ""])
    console.print(f"[green]CSV saved → {path}[/green]")
