from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from units.compat import mock
from units.compat import unittest

# just for quick local test
# import unittest
# from unittest import mock

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

from ansible.modules.cloud.vmware import vmware_host_sriov
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


def gen_mock_attrs(user_input):
    mock_attrs = dict(user_input)
    mock_attrs["results"] = {"before": {}, "after": {}, "changes": {}}
    mock_host = mock.Mock()
    mock_attrs["hosts"] = [mock_host]
    return mock_attrs


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    if arg.endswith("my_command"):
        return "/usr/bin/my_command"
    else:
        if required:
            fail_json(msg="%r not found !" % arg)


test_data = [
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": -4,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": AnsibleFailJson(
            {"msg": "allowed value for num_virt_func >= 0", "failed": True}
        ),
    },
    # 1. num_virt_func == 0, sriov_on == True
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 0,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": AnsibleFailJson(
            {
                "msg": "with sriov_on == true,  alowed value for num_virt_func > 0",
                "failed": True,
            }
        ),
    },
    # 2. num_virt_func > 0, sriov_on == False
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": False,
            "num_virt_func": 5,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": AnsibleFailJson(
            {
                "msg": "with sriov_on == false,  alowed value for num_virt_func is 0",
                "failed": True,
            }
        ),
    },
    # 3.  not supported sriov
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 0,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": False,
        },
        "expected": AnsibleFailJson(
            {
                "msg": "sriov not supported on host= test_host, nic= vmnic0",
                "failed": True,
            }
        ),
    },
    # 4.  not suported num_virt_func
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 4,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": AnsibleFailJson(
            {"msg": "maxVirtualFunctionSupported= 4 on vmnic0", "failed": True}
        ),
    },
    # 5. normal enabling
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": False,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 0,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": {
            "sriovEnabled": True,
            "numVirtualFunction": 8,
            "msg": "",
            "change": True,
            "changes": {"numVirtualFunction": 8, "sriovEnabled": True},
        },
    },
    # 6. already eanabled, not active
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": False,
            "sriovEnabled": True,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 0,
            "numVirtualFunctionRequested": 8,
            "rebootRequired": True,
            "sriovCapable": True,
        },
        "expected": {
            "sriovEnabled": True,
            "numVirtualFunction": 8,
            "msg": "",
            "change": False,
            "changes": {
                "msg": "Not active (looks not rebooted) No any changes, already configured "
            },
        },
    },
    # 7. already eanabled and active
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": True,
            "sriovEnabled": True,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 8,
            "numVirtualFunctionRequested": 8,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": {
            "sriovEnabled": True,
            "numVirtualFunction": 8,
            "msg": "",
            "change": False,
            "changes": {"msg": "No any changes, already configured "},
        },
    },
    # 8. already eanabled diff numVirtualFunction
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": True,
            "num_virt_func": 8,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": True,
            "sriovEnabled": True,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 4,
            "numVirtualFunctionRequested": 4,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": {
            "sriovEnabled": True,
            "numVirtualFunction": 8,
            "msg": "",
            "change": True,
            "changes": {"numVirtualFunction": 8},
        },
    },
    # 9.  disable sriov
    {
        "user_input": {
            "hostname": "test_vCenter",
            "esxi_host_name": "test_host",
            "sriov_on": False,
            "num_virt_func": 0,
            "vmnic": "vmnic0",
        },
        "before": {
            "sriovActive": True,
            "sriovEnabled": True,
            "maxVirtualFunctionSupported": 63,
            "numVirtualFunction": 8,
            "numVirtualFunctionRequested": 8,
            "rebootRequired": False,
            "sriovCapable": True,
        },
        "expected": {
            "sriovEnabled": False,
            "numVirtualFunction": 0,
            "msg": "",
            "change": True,
            "changes": {"sriovEnabled": False, "numVirtualFunction": 0},
        },
    },
]


class TestAdapterMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(
        vmware_host_sriov.VmwareAdapterConfigManager, "__init__", return_value=None
    )
    def test_sanitize_params(self, mock__init__):
        for num, case in enumerate(test_data):
            config = vmware_host_sriov.VmwareAdapterConfigManager()
            config.module = mock.Mock()
            config.module.check_mode = False
            config.module.fail_json.side_effect = fail_json

            config.__dict__.update(gen_mock_attrs(case["user_input"]))
            print("config=", config.__dict__)

            try:
                result = config.sanitize_params(
                    case["before"],
                    case["user_input"]["esxi_host_name"],
                    case["user_input"]["vmnic"],
                )
                # print(">>>" + "test=" + str(num), result)
                self.assertIsInstance(result, type(case["expected"]), "test=" + str(num))
                self.assertEqual(result, case["expected"], "test=" + str(num))

            except Exception as e:
                # print(">>>" + "test=" + str(num), e)
                self.assertIsInstance(e, type(case["expected"]), "test=" + str(num))
                self.assertEqual(e.args[0], case["expected"].args[0], "test=" + str(num))


if __name__ == "__main__":
    unittest.main()
