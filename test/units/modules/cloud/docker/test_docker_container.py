import unittest

from ansible.modules.cloud.docker.docker_container import TaskParameters


class TestTaskParameters(unittest.TestCase):
    """Unit tests for TaskParameters."""

    def test_parse_exposed_ports_tcp_udp(self):
        """
        Ensure _parse_exposed_ports does not cancel ports with the same
        number but different protocol.
        """
        task_params = TaskParameters.__new__(TaskParameters)
        task_params.exposed_ports = None
        result = task_params._parse_exposed_ports([80, '443', '443/udp'])
        self.assertTrue((80, 'tcp') in result)
        self.assertTrue((443, 'tcp') in result)
        self.assertTrue((443, 'udp') in result)
