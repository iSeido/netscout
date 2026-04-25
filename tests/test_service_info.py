from scanner.service_info import get_service_name, TOP_PORTS


def test_known_ports():
    assert get_service_name(22) == "SSH"
    assert get_service_name(80) == "HTTP"
    assert get_service_name(443) == "HTTPS"
    assert get_service_name(3389) == "RDP"
    assert get_service_name(3306) == "MySQL"


def test_unknown_port_returns_unknown():
    assert get_service_name(12345) == "unknown"
    assert get_service_name(1) == "unknown"


def test_top_ports_keys_exist():
    assert set(TOP_PORTS.keys()) == {20, 50, 100}


def test_top_ports_counts():
    assert len(TOP_PORTS[20]) == 15
    assert len(TOP_PORTS[50]) == 50
    assert len(TOP_PORTS[100]) == 100


def test_top_ports_contain_common_ports():
    for tier in TOP_PORTS.values():
        assert 22 in tier
        assert 80 in tier
        assert 443 in tier
