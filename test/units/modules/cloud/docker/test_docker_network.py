import unittest

from ansible.modules.cloud.docker.docker_network import get_ip_version


class TestDockerNetwork(unittest.TestCase):
    """Unit tests for docker_network."""

    def test_get_ip_version(self):
        """Ensure get_ip_version correctly identifies IP version of a valid CIDR."""

        self.assertEqual(get_ip_version('192.168.0.1/16'), 'ipv4')
        self.assertEqual(get_ip_version('192.168.0.1/24'), 'ipv4')
        self.assertEqual(get_ip_version('192.168.0.1/32'), 'ipv4')

        self.assertEqual(get_ip_version('fdd1:ac8c:0557:7ce2::/64'), 'ipv6')
        self.assertEqual(get_ip_version('fdd1:ac8c:0557:7ce2::/128'), 'ipv6')

        # not valid IPv4 or IPv6 subnet resulting in default 'ipv6'
        self.assertEqual(get_ip_version('192.168.0.1'), 'ipv6')
        self.assertEqual(get_ip_version('192.168.0.1/34'), 'ipv6')
        self.assertEqual(get_ip_version('192.168.0.1/asd'), 'ipv6')
        self.assertEqual(get_ip_version('fdd1:ac8c:0557:7ce2::'), 'ipv6')
