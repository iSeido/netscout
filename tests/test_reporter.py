import csv
import json

from scanner.port_scanner import HostResult, PortResult
from scanner.reporter import export_json, export_csv


def _make_results() -> list[HostResult]:
    return [
        HostResult(
            ip="192.168.1.1",
            ports=[
                PortResult(port=22, state="open", service="SSH", banner="OpenSSH_8.9"),
                PortResult(port=80, state="open", service="HTTP", banner=None),
                PortResult(port=9999, state="closed", service="unknown", banner=None),
            ],
        ),
        HostResult(
            ip="192.168.1.2",
            ports=[
                PortResult(port=443, state="open", service="HTTPS", banner=None),
            ],
        ),
    ]


class TestExportJson:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "results.json"
        export_json(_make_results(), str(out))
        assert out.exists()

    def test_structure(self, tmp_path):
        out = tmp_path / "results.json"
        export_json(_make_results(), str(out))
        data = json.loads(out.read_text())
        assert len(data) == 2
        assert data[0]["ip"] == "192.168.1.1"
        assert len(data[0]["open_ports"]) == 2

    def test_closed_ports_excluded(self, tmp_path):
        out = tmp_path / "results.json"
        export_json(_make_results(), str(out))
        data = json.loads(out.read_text())
        ports = [p["port"] for p in data[0]["open_ports"]]
        assert 9999 not in ports

    def test_banner_preserved(self, tmp_path):
        out = tmp_path / "results.json"
        export_json(_make_results(), str(out))
        data = json.loads(out.read_text())
        ssh = next(p for p in data[0]["open_ports"] if p["port"] == 22)
        assert ssh["banner"] == "OpenSSH_8.9"

    def test_host_with_no_open_ports_excluded(self, tmp_path):
        results = [HostResult(ip="10.0.0.1", ports=[
            PortResult(port=80, state="closed", service="HTTP", banner=None),
        ])]
        out = tmp_path / "results.json"
        export_json(results, str(out))
        data = json.loads(out.read_text())
        assert data == []


class TestExportCsv:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "results.csv"
        export_csv(_make_results(), str(out))
        assert out.exists()

    def test_header_row(self, tmp_path):
        out = tmp_path / "results.csv"
        export_csv(_make_results(), str(out))
        with open(out, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == ["ip", "port", "service", "banner"]

    def test_row_count(self, tmp_path):
        out = tmp_path / "results.csv"
        export_csv(_make_results(), str(out))
        with open(out, newline="") as f:
            rows = list(csv.reader(f))
        # header + 2 open ports on host1 + 1 open port on host2
        assert len(rows) == 4

    def test_closed_ports_excluded(self, tmp_path):
        out = tmp_path / "results.csv"
        export_csv(_make_results(), str(out))
        with open(out, newline="") as f:
            content = f.read()
        assert "9999" not in content

    def test_empty_banner_written_as_blank(self, tmp_path):
        out = tmp_path / "results.csv"
        export_csv(_make_results(), str(out))
        with open(out, newline="") as f:
            rows = list(csv.reader(f))
        http_row = next(r for r in rows[1:] if r[1] == "80")
        assert http_row[3] == ""
