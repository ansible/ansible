from __future__ import absolute_import, division, print_function
__metaclass__ = type

# do not execute test if mock is not available
import sys
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    exit()

import unittest
from unittest import mock

from ansible.modules.cloud.vmware import vmware_host_sriov
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


mock_host = mock.Mock()
mock_host.name = "test_host"
tests = [
    # 1. normal activate
    {
        "pnic_info": {
            "sriovCapable": True,
            "sriovEnabled": False,
            "sriovActive": False,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "maxVirtualFunctionSupported": 64,
            "rebootRequired": True,
        },
        "mock_attrs": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriovOn": True,
            "numVirtFunc": 8,
            "vmnic": "vmnic7",
            "results": {"before": {}, "after": {}, "changes": {}},
            "hosts": [mock_host],
        },
        "changes": {
            "test_host": {
                "rebootRequired": True,
                "sriovEnabled": True,
                "numVirtualFunction": 8,
            }
        },
    },
    # 2. already eanabled
    {
        "pnic_info": {
            "sriovCapable": True,
            "sriovEnabled": True,
            "sriovActive": False,
            "numVirtualFunction": 8,
            "numVirtualFunctionRequested": 8,
            "maxVirtualFunctionSupported": 64,
            "rebootRequired": True,
        },
        "mock_attrs": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriovOn": True,
            "numVirtFunc": 8,
            "vmnic": "vmnic7",
            "results": {"before": {}, "after": {}, "changes": {}},
            "hosts": [mock_host],
        },
        "changes": {
            "test_host": {
                "rebootRequired": True,
                "msg": "No any changes, already configured",
            }
        },
    },
    # 3. already active
    {
        "pnic_info": {
            "sriovCapable": True,
            "sriovEnabled": True,
            "sriovActive": True,
            "numVirtualFunction": 8,
            "numVirtualFunctionRequested": 8,
            "maxVirtualFunctionSupported": 64,
            "rebootRequired": False,
        },
        "mock_attrs": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriovOn": True,
            "numVirtFunc": 8,
            "vmnic": "vmnic7",
            "results": {"before": {}, "after": {}, "changes": {}},
            "hosts": [mock_host],
        },
        "changes": {
            "test_host": {
                "rebootRequired": False,
                "msg": "No any changes, already configured",
            }
        },
    },
    # 4. not suported numVirtFunc
    {
        "pnic_info": {
            "sriovCapable": True,
            "sriovEnabled": True,
            "sriovActive": True,
            "numVirtualFunction": 8,
            "numVirtualFunctionRequested": 8,
            "maxVirtualFunctionSupported": 64,
            "rebootRequired": False,
        },
        "mock_attrs": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriovOn": True,
            "numVirtFunc": 100,
            "vmnic": "vmnic7",
            "results": {"before": {}, "after": {}, "changes": {}},
            "hosts": [mock_host],
        },
        "changes": {
            "test_host": {
                "rebootRequired": False,
                "msg": "maxVirtualFunctionSupported= 64 on vmnic7",
            }
        },
    },
    # 5. not supported sriov
    {
        "pnic_info": {
            "sriovCapable": False,
            "sriovEnabled": False,
            "sriovActive": False,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "maxVirtualFunctionSupported": 0,
            "rebootRequired": False,
        },
        "mock_attrs": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriovOn": True,
            "numVirtFunc": 8,
            "vmnic": "vmnic7",
            "results": {"before": {}, "after": {}, "changes": {}},
            "hosts": [mock_host],
        },
        "changes": {
            "test_host": {
                "rebootRequired": False,
                "msg": "sriov not supported on host= test_host, nic= vmnic7",
            }
        },
    },
]


class TestAdapterMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(
        vmware_host_sriov.VmwareAdapterConfigManager,
        "_getPciId",
        return_value="0000:87:00.1",
    )
    @mock.patch.object(
        vmware_host_sriov.VmwareAdapterConfigManager,
        "_check_sriov",
        # there is 2 call _check_sriov in test, need duplicate
        side_effect=[i["pnic_info"] for i in tests for ii in range(2)],
    )
    @mock.patch.object(
        vmware_host_sriov.VmwareAdapterConfigManager, "__init__", return_value=None
    )
    def test_check_host_state(self, mock__init__, mock__check_sriov, mock__getPciId):
        check_sriov_count = 0
        for case in tests:
            config = vmware_host_sriov.VmwareAdapterConfigManager()
            config.module = mock.Mock()
            config.module.check_mode = False
            config.__dict__.update(case["mock_attrs"])
            config.set_host_state()
            self.assertEqual(
                config.results["changes"],
                case["changes"],
                'wrong "changes" in "result"',
            )
            check_sriov_count += 2
            self.assertEqual(
                mock__check_sriov.call_count,
                check_sriov_count,
                "mock__check_sriov called mor or less 2 times",
            )


if __name__ == "__main__":
    unittest.main()
