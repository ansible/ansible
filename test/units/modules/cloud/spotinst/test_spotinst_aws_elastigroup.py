import unittest
import sys
from mock import MagicMock
sys.modules['spotinst_sdk'] = MagicMock()

from ansible.modules.cloud.spotinst.spotinst_aws_elastigroup import expand_elastigroup


class MockModule:

    def __init__(self, input_dict):
        self.params = input_dict


class TestSpotinstAwsElastigroup(unittest.TestCase):
    """Unit test for the spotinst_ocean_cloud module"""

    def test_expand_elastigroup(self):
        """Format input into proper json structure"""

        input_dict = dict(
            name="test_name",
            min_size=1,
            max_size=2,
            target=3,
            product="test_product",
            image_id="test_id",
            health_check_grace_period=0,
            ebs_optimized=True,
            elastic_beanstalk=dict(
                managed_actions=dict(
                    platform_update=dict(
                        perform_at="test_perform_at",
                        time_window="test_time_window",
                        update_level="test_update_level"
                    )
                ),
                deployment_preferences=dict(
                    grace_period=0,
                    batch_size_percentage=100,
                    automatic_roll=True
                )
            )
        )
        module = MockModule(input_dict=input_dict)
        actual_eg = expand_elastigroup(module=module, is_update=False)

        self.assertEqual("test_name", actual_eg.name)

        self.assertEqual(1, actual_eg.capacity.minimum)
        self.assertEqual(2, actual_eg.capacity.maximum)
        self.assertEqual(3, actual_eg.capacity.target)

        self.assertEqual("test_product", actual_eg.compute.product)
        self.assertEqual("test_id", actual_eg.compute.launch_specification.image_id)
        self.assertEqual(0, actual_eg.compute.launch_specification.health_check_grace_period)
        self.assertEqual(True, actual_eg.compute.launch_specification.ebs_optimized)

        self.assertEqual(
            "test_perform_at", actual_eg.third_parties_integration.elastic_beanstalk.managed_actions.platform_update.perform_at)
        self.assertEqual(
            "test_time_window", actual_eg.third_parties_integration.elastic_beanstalk.managed_actions.platform_update.time_window)
        self.assertEqual(
            "test_update_level", actual_eg.third_parties_integration.elastic_beanstalk.managed_actions.platform_update.update_level)

        self.assertEqual(
            0, actual_eg.third_parties_integration.elastic_beanstalk.deployment_preferences.grace_period)
        self.assertEqual(
            100, actual_eg.third_parties_integration.elastic_beanstalk.deployment_preferences.batch_size_percentage)
        self.assertEqual(
            True, actual_eg.third_parties_integration.elastic_beanstalk.deployment_preferences.automatic_roll)
