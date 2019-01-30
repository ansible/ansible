import unittest
import sys
from mock import MagicMock
sys.modules['spotinst_sdk'] = MagicMock()

from ansible.modules.cloud.spotinst.spotinst_ocean_cloud import expand_ocean_request


class MockModule:

    def __init__(self, input_dict):
        self.params = input_dict


class TestSpotinstOceanCloud(unittest.TestCase):
    """Unit test for the spotinst_ocean_cloud module"""

    def test_expand_ocean_request(self):
        """Format input into proper json structure"""

        input_dict = dict(
            name="test_name",
            controller_cluster_id="test_controller_cluster_id",
            region="test_region",
            compute=dict(
                launch_specification=dict(
                    user_data="test_user_data",
                    key_pair="test_key_pair",
                    image_id="test_image_id",
                    security_group_ids=["test_security_group_ids"]
                )
            )
        )
        module = MockModule(input_dict=input_dict)
        actual_ocean = expand_ocean_request(module=module, is_update=False)

        self.assertEqual("test_name", actual_ocean.name)
        self.assertEqual("test_controller_cluster_id", actual_ocean.controller_cluster_id)
        self.assertEqual("test_region", actual_ocean.region)
        self.assertEqual("test_user_data", actual_ocean.compute.launch_specification.user_data)
        self.assertEqual("test_key_pair", actual_ocean.compute.launch_specification.key_pair)
        self.assertEqual("test_image_id", actual_ocean.compute.launch_specification.image_id)
        self.assertEqual(["test_security_group_ids"], actual_ocean.compute.launch_specification.security_group_ids)
