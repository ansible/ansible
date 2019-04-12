# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from io import StringIO
from units.compat.mock import MagicMock

from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader
from ansible.errors import AnsibleError


OPTIONS_DATA = (
    (
        {},
        ("vmware_tools setting: vmware_host"),
    ),
    (
        {
            'ansible_host': '10.0.0.1',
        },
        (
            "vmware_tools setting: vmware_user"
        ),
    ),
    (
        {
            'ansible_host': '10.0.0.1',
            'ansible_vmware_user': 'administrator@vsphere.local'
        },
        (
            "vmware_tools setting: vmware_password"
        ),
    ),
    (
        {
            'ansible_host': '10.0.0.1',
            'ansible_vmware_user': 'administrator@vsphere.local',
            'ansible_vmware_password': 'Secret@123'
        },
        (
            "vmware_tools setting: vm_path"
        ),
    ),
    (
        {
            'ansible_host': '10.0.0.1',
            'ansible_vmware_user': 'administrator@vsphere.local',
            'ansible_vmware_password': 'Secret@123',
            'ansible_vmware_guest_path': 'ha-datacenter/vm/VM_0001'
        },
        (
            "vmware_tools setting: vm_user"
        ),
    ),
    (
        {
            'ansible_host': '10.0.0.1',
            'ansible_vmware_user': 'administrator@vsphere.local',
            'ansible_vmware_password': 'Secret@123',
            'ansible_vmware_guest_path': 'ha-datacenter/vm/VM_0001',
            'ansible_vmware_tools_user': 'root',
        },
        (
            "vmware_tools setting: vm_password"
        ),
    ),
)


class TestConnectionVMware(object):
    @pytest.mark.parametrize('options, expected', ((o, e) for o, e in OPTIONS_DATA))
    def test_set_options(self, options, expected):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = connection_loader.get('vmware_tools', pc, new_stdin)
        with pytest.raises(AnsibleError) as exec_info:
            conn.set_options(var_options=options)
        assert expected in str(exec_info)

    def test_set_options_all(self, monkeypatch):
        pc = PlayContext()
        new_stdin = StringIO()
        options = {
            'ansible_host': '10.0.0.1',
            'ansible_vmware_user': 'administrator@vsphere.local',
            'ansible_vmware_password': 'Secret@123',
            'ansible_vmware_guest_path': 'ha-datacenter/vm/VM_0001',
            'ansible_vmware_tools_user': 'root',
            'ansible_vmware_tools_password': 'guest@123',
        }

        conn = connection_loader.get('vmware_tools', pc, new_stdin)
        conn.set_options(var_options=options)

        mock_establish_connection = MagicMock()
        mock_establish_vm = MagicMock()
        monkeypatch.setattr("ansible.plugins.connection.vmware_tools.Connection._establish_connection", mock_establish_connection)
        monkeypatch.setattr("ansible.plugins.connection.vmware_tools.Connection._establish_vm", mock_establish_vm)

        conn._connect()
