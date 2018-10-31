import unittest

from ansible.modules.cloud.docker.docker_network import get_ip_version


class TestDockerNetwork(unittest.TestCase):
    """Unit tests for docker_network."""

    def test_get_ip_version(self):
        """Ensure get_ip_version correctly identifies IP version of a CIDR string."""

        self.assertEqual(get_ip_version('192.168.0.1/16'), 'ipv4')
        self.assertEqual(get_ip_version('192.168.0.1/24'), 'ipv4')
        self.assertEqual(get_ip_version('192.168.0.1/32'), 'ipv4')

        self.assertEqual(get_ip_version('fdd1:ac8c:0557:7ce2::/64'), 'ipv6')
        self.assertEqual(get_ip_version('fdd1:ac8c:0557:7ce2::/128'), 'ipv6')

        with self.assertRaises(ValueError) as e:
            get_ip_version('192.168.0.1')
        self.assertEqual('"192.168.0.1" is not a valid CIDR', str(e.exception))

        with self.assertRaises(ValueError) as e:
            get_ip_version('192.168.0.1/34')
        self.assertEqual('"192.168.0.1/34" is not a valid CIDR', str(e.exception))

        with self.assertRaises(ValueError) as e:
            get_ip_version('192.168.0.1/asd')
        self.assertEqual('"192.168.0.1/asd" is not a valid CIDR', str(e.exception))

        with self.assertRaises(ValueError) as e:
            get_ip_version('fdd1:ac8c:0557:7ce2::')
        self.assertEqual('"fdd1:ac8c:0557:7ce2::" is not a valid CIDR', str(e.exception))
