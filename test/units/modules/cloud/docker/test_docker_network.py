"""Unit tests for docker_network."""
import pytest

from ansible.modules.cloud.docker.docker_network import get_ip_version


@pytest.mark.parametrize("cidr,expected", [
    ('192.168.0.1/16', 'ipv4'),
    ('192.168.0.1/24', 'ipv4'),
    ('192.168.0.1/32', 'ipv4'),
    ('fdd1:ac8c:0557:7ce2::/64', 'ipv6'),
    ('fdd1:ac8c:0557:7ce2::/128', 'ipv6'),
])
def test_get_ip_version_positives(cidr, expected):
    assert get_ip_version(cidr) == expected


@pytest.mark.parametrize("cidr", [
    '192.168.0.1',
    '192.168.0.1/34',
    '192.168.0.1/asd',
    'fdd1:ac8c:0557:7ce2::',
])
def test_get_ip_version_negatives(cidr):
    with pytest.raises(ValueError) as e:
        get_ip_version(cidr)
    assert '"{0}" is not a valid CIDR'.format(cidr) == str(e.value)
