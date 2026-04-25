# netscout

A Python-based network scanning tool to identify connected devices and open ports on small-office networks. Built to demonstrate Python scripting, networking, and security fundamentals.

## Features

- **Host discovery** — ICMP ping sweep to find live devices on a subnet
- **Port scanning** — concurrent TCP port scanning with configurable thread count
- **Service detection** — maps open ports to known service names (80 → HTTP, 22 → SSH, etc.)
- **Banner grabbing** — optionally reads service banners for fingerprinting
- **Rich terminal output** — colour-coded tables with live progress bars
- **Export** — save results to JSON or CSV for further analysis

## Requirements

- Python 3.10+
- [`rich`](https://github.com/Textualize/rich) (terminal formatting — the only external dependency)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/netscout.git
cd netscout
pip install -r requirements.txt
```

Or install as a CLI tool:

```bash
pip install -e .
netscout 192.168.1.0/24
```

## Usage

```
python netscout.py <target> [options]
```

### Examples

```bash
# Discover all devices on a /24 subnet, scan top 20 common ports
python netscout.py 192.168.1.0/24

# Scan top 100 common ports
python netscout.py 192.168.1.0/24 --top-ports 100

# Scan specific ports
python netscout.py 192.168.1.0/24 -p 22,80,443,3389

# Scan a port range
python netscout.py 192.168.1.0/24 -p 1-1024

# Single host with banner grabbing
python netscout.py 192.168.1.1 --banners

# Host discovery only (no port scan)
python netscout.py 192.168.1.0/24 --discover-only

# Export to JSON
python netscout.py 192.168.1.0/24 -o results.json

# Export to CSV
python netscout.py 192.168.1.0/24 -o results.csv

# Skip ping, scan host directly (useful for hosts that block ICMP)
python netscout.py 192.168.1.1 --no-ping -p 1-1024
```

### All options

| Flag | Description | Default |
|------|-------------|---------|
| `-p, --ports PORTS` | Ports: `80`, `22,80,443`, `1-1024`, or mixed | — |
| `--top-ports N` | Scan top N common ports (20, 50, 100) | `20` |
| `--discover-only` | Ping sweep only, skip port scanning | off |
| `--banners` | Grab service banners from open ports | off |
| `--timeout SEC` | Socket/ping timeout in seconds | `1.0` |
| `--threads N` | Max concurrent port-scan threads per host | `100` |
| `--ping-threads N` | Max concurrent ping threads for discovery | `50` |
| `--no-ping` | Skip discovery, scan target directly | off |
| `--show-closed` | Also show closed ports in output | off |
| `-o, --output FILE` | Export results to `.json` or `.csv` | — |
| `--no-banner` | Suppress ASCII art banner | off |

## Project structure

```
netscout/
├── netscout.py           # CLI entry point & orchestration
├── scanner/
│   ├── discovery.py      # ICMP ping sweep (threaded)
│   ├── port_scanner.py   # TCP port scanning (threaded)
│   ├── service_info.py   # Port → service name registry + curated port lists
│   ├── banner.py         # TCP service banner grabbing
│   └── reporter.py       # Rich terminal tables + JSON/CSV export
├── requirements.txt
├── setup.py
└── .gitignore
```

## How it works

1. **Discovery phase** — sends ICMP pings concurrently across the target CIDR range using Python's `subprocess` module and `ThreadPoolExecutor`
2. **Scan phase** — for each live host, opens TCP sockets (`connect_ex`) to each target port concurrently; marks ports as open/closed/filtered
3. **Banner phase** (optional) — reconnects to open ports and reads the first 1024 bytes to capture service banners
4. **Report phase** — renders results as rich terminal tables; optionally writes JSON or CSV

## Ethical use

> Only scan networks you own or have **explicit written permission** to test. Unauthorised port scanning may be illegal in your jurisdiction and violates most network acceptable use policies.

## License

MIT
