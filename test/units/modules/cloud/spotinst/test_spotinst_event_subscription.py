import unittest
import sys
from mock import MagicMock
sys.modules['spotinst_sdk'] = MagicMock()

from ansible.modules.cloud.spotinst.spotinst_event_subscription import expand_subscription_request


class MockModule:

    def __init__(self, input_dict):
        self.params = input_dict


class TestSpotinstEventSubscription(unittest.TestCase):
    """Unit test for the spotinst_event_subscription module"""

    def test_expand_subscription_request(self):
        """Format input into proper json structure"""

        input_dict = dict(
            resource_id="test_resource_id",
            protocol="test_protocol",
            endpoint="test_endpoint",
            event_type="test_event_type",
            event_format="test_event_format"
        )
        module = MockModule(input_dict=input_dict)
        actual_event_subscription = expand_subscription_request(module=module)

        self.assertEqual("test_resource_id", actual_event_subscription.resource_id)
        self.assertEqual("test_protocol", actual_event_subscription.protocol)
        self.assertEqual("test_endpoint", actual_event_subscription.endpoint)
        self.assertEqual("test_event_type", actual_event_subscription.event_type)
        self.assertEqual("test_event_format", actual_event_subscription.event_format)
