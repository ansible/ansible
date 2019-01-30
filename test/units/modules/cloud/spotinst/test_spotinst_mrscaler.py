import unittest
import sys
from mock import MagicMock
sys.modules['spotinst_sdk'] = MagicMock()

from ansible.modules.cloud.spotinst.spotinst_mrscaler import expand_emr_request


class MockModule:

    def __init__(self, input_dict):
        self.params = input_dict


class TestSpotinstMrScaler(unittest.TestCase):
    """Unit test for the spotinst_spotinst_emr module"""

    def test_expand_emr_request(self):
        """Format input into proper json structure"""

        input_dict = dict(
            name="test_name",
            strategy=dict(
                new=dict(
                    release_label="emr-5.17.0"
                )
            ),
            compute=dict(
                instance_groups=dict(
                    master_group=dict(
                        life_cycle="SPOT",
                        target=0
                    ),
                    core_group=dict(
                        target=1,
                        life_cycle="ON_DEMAND"
                    )
                )
            )
        )

        module = MockModule(input_dict=input_dict)
        actual_mrScaler = expand_emr_request(module=module, is_update=False)

        self.assertEqual("test_name", actual_mrScaler.name)

        self.assertEqual("emr-5.17.0", actual_mrScaler.strategy.new.release_label)

        self.assertEqual("SPOT", actual_mrScaler.compute.instance_groups.master_group.life_cycle)
        self.assertEqual(0, actual_mrScaler.compute.instance_groups.master_group.target)

        self.assertEqual("ON_DEMAND", actual_mrScaler.compute.instance_groups.core_group.life_cycle)
        self.assertEqual(1, actual_mrScaler.compute.instance_groups.core_group.target)
