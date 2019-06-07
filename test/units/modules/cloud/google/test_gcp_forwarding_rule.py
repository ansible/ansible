import unittest

from ansible.modules.cloud.google._gcp_forwarding_rule import _build_global_forwarding_rule_dict


class TestGCPFowardingRule(unittest.TestCase):
    """Unit tests for gcp_fowarding_rule module."""
    params_dict = {
        'forwarding_rule_name': 'foo_fowarding_rule_name',
        'address': 'foo_external_address',
        'target': 'foo_targetproxy',
        'region': 'global',
        'port_range': 80,
        'protocol': 'TCP',
        'state': 'present',
    }

    def test__build_global_forwarding_rule_dict(self):

        expected = {
            'name': 'foo_fowarding_rule_name',
            'IPAddress': 'https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/foo_external_address',
            'target': 'https://www.googleapis.com/compute/v1/projects/my-project/global/targetHttpProxies/foo_targetproxy',
            'region': 'global',
            'portRange': 80,
            'IPProtocol': 'TCP',
        }
        actual = _build_global_forwarding_rule_dict(
            self.params_dict, 'my-project')
        self.assertEqual(expected, actual)
