# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import sys
import pytest

pyvmomi = pytest.importorskip('pyVmomi')

from ansible.module_utils.vmware import connect_to_api, PyVmomi


test_data = [
    (
        dict(
            username='Administrator@vsphere.local',
            password='Esxi@123$%',
            hostname=False,
            validate_certs=False,
        ),
        "Hostname parameter is missing. Please specify this parameter in task or"
        " export environment variable like 'export VMWARE_HOST=ESXI_HOSTNAME'"
    ),
    (
        dict(
            username=False,
            password='Esxi@123$%',
            hostname='esxi1',
            validate_certs=False,
        ),
        "Username parameter is missing. Please specify this parameter in task or"
        " export environment variable like 'export VMWARE_USER=ESXI_USERNAME'"
    ),
    (
        dict(
            username='Administrator@vsphere.local',
            password=False,
            hostname='esxi1',
            validate_certs=False,
        ),
        "Password parameter is missing. Please specify this parameter in task or"
        " export environment variable like 'export VMWARE_PASSWORD=ESXI_PASSWORD'"
    ),
    (
        dict(
            username='Administrator@vsphere.local',
            password='Esxi@123$%',
            hostname='esxi1',
            validate_certs=True,
        ),
        "Unknown error while connecting to vCenter or ESXi API at esxi1:443"
    ),
]


class AnsibleModuleExit(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ExitJson(AnsibleModuleExit):
    pass


class FailJson(AnsibleModuleExit):
    pass


@pytest.fixture
def fake_ansible_module():
    return FakeAnsibleModule()


class FakeAnsibleModule:
    def __init__(self):
        self.params = {}
        self.tmpdir = None

    def exit_json(self, *args, **kwargs):
        raise ExitJson(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        raise FailJson(*args, **kwargs)


def fake_connect_to_api(module):
    pass


def test_pyvmomi_lib_exists(mocker, fake_ansible_module):
    """ Test if Pyvmomi is present or not"""
    mocker.patch('ansible.module_utils.vmware.HAS_PYVMOMI', new=False)
    with pytest.raises(FailJson) as exec_info:
        PyVmomi(fake_ansible_module)

    assert 'Failed to import the required Python library (PyVmomi) on' in exec_info.value.kwargs['msg']


def test_requests_lib_exists(mocker, fake_ansible_module):
    """ Test if requests is present or not"""
    mocker.patch('ansible.module_utils.vmware.HAS_REQUESTS', new=False)
    with pytest.raises(FailJson) as exec_info:
        PyVmomi(fake_ansible_module)

    assert 'Failed to import the required Python library (requests) on' in exec_info.value.kwargs['msg']


@pytest.mark.skipif(sys.version_info < (2, 7), reason="requires python2.7 and greater")
@pytest.mark.parametrize("params, msg", test_data, ids=['hostname', 'username', 'password', 'validate_certs'])
def test_required_params(request, params, msg, fake_ansible_module):
    """ Test if required params are correct or not"""
    fake_ansible_module.params = params
    with pytest.raises(FailJson) as exec_info:
        connect_to_api(fake_ansible_module)
    assert msg in exec_info.value.kwargs['msg']


def test_validate_certs(mocker, fake_ansible_module):
    """ Test if SSL is required or not"""
    fake_ansible_module.params = test_data[3][0]

    mocker.patch('ansible.module_utils.vmware.ssl', new=None)
    with pytest.raises(FailJson) as exec_info:
        PyVmomi(fake_ansible_module)
    msg = 'pyVim does not support changing verification mode with python < 2.7.9.' \
          ' Either update python or use validate_certs=false.'
    assert msg == exec_info.value.kwargs['msg']


def test_vmdk_disk_path_split(mocker, fake_ansible_module):
    """ Test vmdk_disk_path_split function"""
    fake_ansible_module.params = test_data[0][0]

    mocker.patch('ansible.module_utils.vmware.connect_to_api', new=fake_connect_to_api)
    pyv = PyVmomi(fake_ansible_module)
    v = pyv.vmdk_disk_path_split('[ds1] VM_0001/VM0001_0.vmdk')
    assert v == ('ds1', 'VM_0001/VM0001_0.vmdk', 'VM0001_0.vmdk', 'VM_0001')


def test_vmdk_disk_path_split_negative(mocker, fake_ansible_module):
    """ Test vmdk_disk_path_split function"""
    fake_ansible_module.params = test_data[0][0]

    mocker.patch('ansible.module_utils.vmware.connect_to_api', new=fake_connect_to_api)
    with pytest.raises(FailJson) as exec_info:
        pyv = PyVmomi(fake_ansible_module)
        pyv.vmdk_disk_path_split('[ds1]')

    assert 'Bad path' in exec_info.value.kwargs['msg']
