import errno
from unittest.mock import MagicMock, patch

from scanner.port_scanner import _scan_port

_TIMEDOUT = getattr(errno, "ETIMEDOUT", getattr(errno, "WSAETIMEDOUT", 10060))
_REFUSED = getattr(errno, "ECONNREFUSED", getattr(errno, "WSAECONNREFUSED", 10061))


def _mock_sock(connect_ex_return):
    sock = MagicMock()
    sock.connect_ex.return_value = connect_ex_return
    return sock


def test_zero_is_open():
    with patch("scanner.port_scanner.socket.socket", return_value=_mock_sock(0)):
        r = _scan_port("127.0.0.1", 80, 1.0, False)
    assert r.state == "open"


def test_connection_refused_is_closed():
    with patch("scanner.port_scanner.socket.socket", return_value=_mock_sock(_REFUSED)):
        r = _scan_port("127.0.0.1", 9999, 1.0, False)
    assert r.state == "closed"


def test_timeout_errno_is_filtered():
    with patch("scanner.port_scanner.socket.socket", return_value=_mock_sock(_TIMEDOUT)):
        r = _scan_port("127.0.0.1", 9999, 1.0, False)
    assert r.state == "filtered"
