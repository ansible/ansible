import unittest

from ansible.plugins.action import add_host


class TestAddHost(unittest.TestCase):

    def test_hostname(self):
        host, port = add_host._parse_ip_host_and_port('some-remote-host')
        assert host == 'some-remote-host'
        assert port is None

    def test_hostname_with_port(self):
        host, port = add_host._parse_ip_host_and_port('some-remote-host:80')
        assert host == 'some-remote-host'
        assert port == '80'

    def test_parse_ip_host_and_port_v4(self):
        host, port = add_host._parse_ip_host_and_port('8.8.8.8')
        assert host == '8.8.8.8'
        assert port is None

    def test_parse_ip_host_and_port_v4_and_port(self):
        host, port = add_host._parse_ip_host_and_port('8.8.8.8:80')
        assert host == '8.8.8.8'
        assert port == '80'

    def test_parse_ip_host_and_port_v6(self):
        host, port = add_host._parse_ip_host_and_port(
            'dead:beef:dead:beef:dead:beef:dead:beef'
        )
        assert host == 'dead:beef:dead:beef:dead:beef:dead:beef'
        assert port is None

    def test_parse_ip_host_and_port_v6_with_brackets(self):
        host, port = add_host._parse_ip_host_and_port(
            '[dead:beef:dead:beef:dead:beef:dead:beef]'
        )
        assert host == 'dead:beef:dead:beef:dead:beef:dead:beef'
        assert port is None

    def test_parse_ip_host_and_port_v6_with_brackets_and_port(self):
        host, port = add_host._parse_ip_host_and_port(
            '[dead:beef:dead:beef:dead:beef:dead:beef]:80'
        )
        assert host == 'dead:beef:dead:beef:dead:beef:dead:beef'
        assert port == '80'
