# netscout

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

A Python-based network scanning tool to identify connected devices and open ports on small-office networks.  
Built as a portfolio project to demonstrate Python scripting, networking concepts, and security fundamentals.

---

## Features

| Feature | Description |
|---------|-------------|
| Host Discovery | ICMP ping sweep — finds every live device on the subnet |
| Port Scanning | Concurrent TCP scanning across hundreds of ports in seconds |
| Service Detection | Maps open ports to service names (22 → SSH, 80 → HTTP, 3389 → RDP, etc.) |
| Banner Grabbing | Reads service banners to identify software versions |
| Rich Output | Colour-coded terminal tables with live progress bars |
| Export | Save results to JSON or CSV for reporting / further analysis |

---

## Requirements

- Python 3.10+
- [`rich`](https://github.com/Textualize/rich) — the only external dependency (terminal UI)

All other functionality uses Python stdlib: `socket`, `subprocess`, `concurrent.futures`, `ipaddress`.

---

## Installation

```bash
git clone https://github.com/ahmadsufean/netscout.git
cd netscout
pip install -r requirements.txt
```

Optional — install as a system CLI tool:

```bash
pip install -e .
netscout 192.168.1.0/24
```

---

## Usage

```
python netscout.py <target> [options]
```

### Common examples

```bash
# Scan your whole /24 subnet (top 20 common ports)
python netscout.py 192.168.1.0/24

# Scan top 100 ports
python netscout.py 192.168.1.0/24 --top-ports 100

# Scan specific ports
python netscout.py 192.168.1.0/24 -p 22,80,443,3389

# Scan a full port range
python netscout.py 192.168.1.0/24 -p 1-1024

# Single host with banner grabbing
python netscout.py 192.168.1.1 --banners

# Discovery only — just find live devices, no port scan
python netscout.py 192.168.1.0/24 --discover-only

# Skip ping (useful for hosts that block ICMP)
python netscout.py 192.168.1.1 --no-ping -p 1-1024

# Export results to JSON
python netscout.py 192.168.1.0/24 -o results.json

# Export results to CSV
python netscout.py 192.168.1.0/24 -o results.csv
```

### All options

| Flag | Description | Default |
|------|-------------|---------|
| `-p, --ports PORTS` | Ports to scan: `80`, `22,80,443`, `1-1024`, or mixed | — |
| `--top-ports N` | Scan top N common ports: `20`, `50`, or `100` | `20` |
| `--discover-only` | Ping sweep only — skip port scanning | off |
| `--banners` | Grab service banners from open ports | off |
| `--timeout SEC` | Socket/ping timeout in seconds | `1.0` |
| `--threads N` | Max concurrent port-scan threads per host | `100` |
| `--ping-threads N` | Max concurrent ping threads for host discovery | `50` |
| `--no-ping` | Skip discovery, scan target directly | off |
| `--show-closed` | Display closed ports in output too | off |
| `-o, --output FILE` | Export results to `.json` or `.csv` | — |
| `--no-banner` | Suppress ASCII art banner | off |

---

## How it works

```
Target CIDR
    │
    ▼
┌─────────────────────┐
│  Phase 1: Discovery │  Threaded ping sweep via subprocess
│  (ping sweep)       │  ThreadPoolExecutor — 50 workers default
└────────┬────────────┘
         │  live hosts
         ▼
┌─────────────────────┐
│  Phase 2: Port Scan │  TCP connect_ex per port
│  (TCP connect)      │  ThreadPoolExecutor — 100 workers default
└────────┬────────────┘
         │  open ports
         ▼
┌─────────────────────┐
│  Phase 3: Report    │  Rich tables in terminal
│  (optional export)  │  JSON / CSV output
└─────────────────────┘
```

1. **Discovery** — `subprocess` pings each IP in the CIDR range concurrently. Live hosts are collected.
2. **Scanning** — for each live host, `socket.connect_ex()` tests each port. Ports get marked `open`, `closed`, or `filtered`.
3. **Banners** (optional) — reconnects to open ports, reads up to 1024 bytes, extracts first line of response.
4. **Report** — renders colour-coded tables via `rich`; optionally writes JSON/CSV.

---

## Project structure

```
netscout/
├── netscout.py           # CLI entry point, argparse, orchestration
├── scanner/
│   ├── discovery.py      # ICMP ping sweep
│   ├── port_scanner.py   # TCP port scanning + PortResult/HostResult dataclasses
│   ├── service_info.py   # Port → service name registry + curated top-port lists
│   ├── banner.py         # TCP banner grabbing
│   └── reporter.py       # Rich terminal output + JSON/CSV export
├── requirements.txt
├── setup.py
└── .gitignore
```

---

## Ethical use

> **Only scan networks you own or have explicit written permission to test.**  
> Unauthorised port scanning may be illegal in your jurisdiction and violates most network acceptable use policies.

---

## Author

**Ahmed Maghrabi** — [GitHub](https://github.com/ahmadsufean)

---

## License

MIT — free to use, modify, and distribute.
