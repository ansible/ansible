#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_vsan
from ansible.modules.network.nxos.nxos_vsan import GetVsanInfoFromSwitch

from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVsanModule(TestNxosModule):

    module = nxos_vsan

    def setUp(self):
        super(TestNxosVsanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vsan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_execute_show_vsan_cmd = patch('ansible.modules.network.nxos.nxos_vsan.GetVsanInfoFromSwitch.execute_show_vsan_cmd')
        self.execute_show_vsan_cmd = self.mock_execute_show_vsan_cmd.start()

        self.mock_execute_show_vsanmemcmd = patch('ansible.modules.network.nxos.nxos_vsan.GetVsanInfoFromSwitch.execute_show_vsan_mem_cmd')
        self.execute_show_vsanmem_cmd = self.mock_execute_show_vsanmemcmd.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vsan.load_config')
        self.load_config = self.mock_load_config.start()

        self.maxDiff = None

    def tearDown(self):
        super(TestNxosVsanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.execute_show_vsan_cmd.stop()
        self.execute_show_vsanmem_cmd.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_vsan_add_remove_but_present_in_switch(self):
        margs = {
            "vsan": [
                {
                    "interface": [
                        "fc1/1",
                        "port-channel 55"
                    ],
                    "id": 922,
                    "remove": False,
                    "name": "vsan-SAN-A"
                },
                {
                    "interface": [
                        "fc1/11",
                        "fc1/21",
                        "port-channel 56"
                    ],
                    "id": 923,
                    "remove": False,
                    "name": "vsan-SAN-B"
                },
                {
                    "id": 1923,
                    "remove": True,
                    "name": "vsan-SAN-Old"
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_vsan_remove(self):
        margs = {
            "vsan": [
                {
                    "id": 922,
                    "remove": True
                },
                {
                    "id": 923,
                    "remove": True
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ["terminal dont-ask"] + ["vsan database"] + ["no vsan 922", "no vsan 923"] + ["no terminal dont-ask"])

    def test_vsan_add(self):
        margs = {
            "vsan": [
                {
                    "interface": [
                        "fc1/1",
                        "port-channel 55"
                    ],
                    "id": 924,
                    "name": "vsan-SAN-924"
                },
                {
                    "interface": [
                        "fc1/11",
                        "fc1/21",
                        "port-channel 56"
                    ],
                    "id": 925,
                    "name": "vsan-SAN-925"
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ["terminal dont-ask"] + ["vsan database"] +
                         ["vsan 924", "vsan 924 name vsan-SAN-924", "no vsan 924 suspend", "vsan 924 interface fc1/1", "vsan 924 interface port-channel 55"] +
                         ["vsan 925", "vsan 925 name vsan-SAN-925", "no vsan 925 suspend", "vsan 925 interface fc1/11", "vsan 925 interface fc1/21", "vsan 925 interface port-channel 56"] +
                         ["no terminal dont-ask"])

    def test_vsan_suspend(self):
        margs = {
            "vsan": [
                {
                    "interface": [
                        "fc1/1",
                        "port-channel 55"
                    ],
                    "id": 924,
                    "name": "vsan-SAN-924"
                },
                {
                    "id": 925,
                    "name": "vsan-SAN-925",
                    "suspend": True
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ["terminal dont-ask"] + ["vsan database"] +
                         ["vsan 924", "vsan 924 name vsan-SAN-924", "no vsan 924 suspend", "vsan 924 interface fc1/1", "vsan 924 interface port-channel 55"] +
                         ["vsan 925", "vsan 925 name vsan-SAN-925", "vsan 925 suspend"] +
                         ["no terminal dont-ask"])

    def test_vsan_invalid_vsan(self):
        margs = {
            "vsan": [
                {
                    "id": 4096,
                    "name": "vsan-SAN-925",
                    "suspend": True
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
            testdata = errinfo.value.args[0]
            assert 'invalid vsan' in str(testdata['msg'])
            assert testdata['failed']

    def test_vsan_change_reserved_vsan(self):
        margs = {
            "vsan": [
                {
                    "id": 4094,
                    "name": "vsan-SAN-925",
                    "suspend": True
                }
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=False)
        assert 'reserved vsan' in str(result['messages'])
        self.assertEqual(result['commands'], [])

    def test_vsan_add_int_existing_vsan(self):
        margs = {
            "vsan": [
                {
                    "interface": [
                        "fc1/1",
                        "fc1/40",
                        "port-channel 155"
                    ],
                    "id": 922,
                },
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ["terminal dont-ask"] + ["vsan database"] +
                         ["vsan 922 interface fc1/40", "vsan 922 interface port-channel 155"] +
                         ["no terminal dont-ask"])

    def test_vsan_remove_non_existing_vsan(self):
        margs = {
            "vsan": [
                {
                    "id": 1111,
                    "remove": True
                },
            ]
        }
        set_module_args(margs)
        self.execute_show_vsan_cmd.return_value = load_fixture('nxos_vsan', 'shvsan.cfg')
        self.execute_show_vsanmem_cmd.return_value = load_fixture('nxos_vsan', 'shvsanmem.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])
        assert 'no vsan' in str(result['messages'])
