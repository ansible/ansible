# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import ssl
import sys
import pytest

pyvmomi = pytest.importorskip('pyVmomi')

from units.compat import mock

import ansible.module_utils.vmware as vmware_module_utils


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


class FailJsonException(BaseException):
    pass


@pytest.fixture
def fake_ansible_module():
    ret = mock.Mock()
    ret.params = test_data[3][0]
    ret.tmpdir = None
    ret.fail_json.side_effect = FailJsonException()
    return ret


def fake_connect_to_api(module, return_si=None):
    return mock.Mock()


testdata = [
    ('HAS_PYVMOMI', 'PyVmomi'),
    ('HAS_REQUESTS', 'requests'),
]


@pytest.mark.parametrize("key,libname", testdata)
def test_lib_loading_failure(monkeypatch, fake_ansible_module, key, libname):
    """ Test if Pyvmomi is present or not"""
    monkeypatch.setattr(vmware_module_utils, key, False)
    with pytest.raises(FailJsonException):
        vmware_module_utils.PyVmomi(fake_ansible_module)
    error_str = 'Failed to import the required Python library (%s)' % libname
    assert fake_ansible_module.fail_json.called_once()
    assert error_str in fake_ansible_module.fail_json.call_args[1]['msg']


@pytest.mark.skipif(sys.version_info < (2, 7), reason="requires python2.7 and greater")
@pytest.mark.parametrize("params, msg", test_data, ids=['hostname', 'username', 'password', 'validate_certs'])
def test_required_params(request, params, msg, fake_ansible_module):
    """ Test if required params are correct or not"""
    fake_ansible_module.params = params
    with pytest.raises(FailJsonException):
        vmware_module_utils.connect_to_api(fake_ansible_module)
    assert fake_ansible_module.fail_json.called_once()
    assert msg in fake_ansible_module.fail_json.call_args[1]['msg']


def test_validate_certs(monkeypatch, fake_ansible_module):
    """ Test if SSL is required or not"""
    fake_ansible_module.params = test_data[3][0]

    monkeypatch.setattr(vmware_module_utils, 'ssl', None)
    with pytest.raises(FailJsonException):
        vmware_module_utils.PyVmomi(fake_ansible_module)
    msg = 'pyVim does not support changing verification mode with python < 2.7.9.' \
          ' Either update python or use validate_certs=false.'
    assert fake_ansible_module.fail_json.called_once()
    assert msg in fake_ansible_module.fail_json.call_args[1]['msg']


def test_vmdk_disk_path_split(monkeypatch, fake_ansible_module):
    """ Test vmdk_disk_path_split function"""
    fake_ansible_module.params = test_data[0][0]

    monkeypatch.setattr(vmware_module_utils, 'connect_to_api', fake_connect_to_api)
    pyv = vmware_module_utils.PyVmomi(fake_ansible_module)
    v = pyv.vmdk_disk_path_split('[ds1] VM_0001/VM0001_0.vmdk')
    assert v == ('ds1', 'VM_0001/VM0001_0.vmdk', 'VM0001_0.vmdk', 'VM_0001')


def test_vmdk_disk_path_split_negative(monkeypatch, fake_ansible_module):
    """ Test vmdk_disk_path_split function"""
    fake_ansible_module.params = test_data[0][0]

    monkeypatch.setattr(vmware_module_utils, 'connect_to_api', fake_connect_to_api)
    with pytest.raises(FailJsonException):
        pyv = vmware_module_utils.PyVmomi(fake_ansible_module)
        pyv.vmdk_disk_path_split('[ds1]')
    assert fake_ansible_module.fail_json.called_once()
    assert 'Bad path' in fake_ansible_module.fail_json.call_args[1]['msg']


@pytest.mark.skipif(sys.version_info < (2, 7), reason="requires python2.7 and greater")
def test_connect_to_api_validate_certs(monkeypatch, fake_ansible_module):
    monkeypatch.setattr(vmware_module_utils, 'connect', mock.Mock())

    def MockSSLContext(proto):
        ssl_context.proto = proto
        return ssl_context

    # New Python with SSLContext + validate_certs=True
    vmware_module_utils.connect.reset_mock()
    ssl_context = mock.Mock()
    monkeypatch.setattr(vmware_module_utils.ssl, 'SSLContext', MockSSLContext)
    fake_ansible_module.params['validate_certs'] = True
    vmware_module_utils.connect_to_api(fake_ansible_module)
    assert ssl_context.proto == ssl.PROTOCOL_SSLv23
    assert ssl_context.verify_mode == ssl.CERT_REQUIRED
    assert ssl_context.check_hostname is True
    vmware_module_utils.connect.SmartConnect.assert_called_once_with(
        host='esxi1',
        port=443,
        pwd='Esxi@123$%',
        user='Administrator@vsphere.local',
        sslContext=ssl_context)

    # New Python with SSLContext + validate_certs=False
    vmware_module_utils.connect.reset_mock()
    ssl_context = mock.Mock()
    monkeypatch.setattr(vmware_module_utils.ssl, 'SSLContext', MockSSLContext)
    fake_ansible_module.params['validate_certs'] = False
    vmware_module_utils.connect_to_api(fake_ansible_module)
    assert ssl_context.proto == ssl.PROTOCOL_SSLv23
    assert ssl_context.verify_mode == ssl.CERT_NONE
    assert ssl_context.check_hostname is False
    vmware_module_utils.connect.SmartConnect.assert_called_once_with(
        host='esxi1',
        port=443,
        pwd='Esxi@123$%',
        user='Administrator@vsphere.local',
        sslContext=ssl_context)

    # Old Python with no SSLContext + validate_certs=True
    vmware_module_utils.connect.reset_mock()
    ssl_context = mock.Mock()
    ssl_context.proto = None
    monkeypatch.delattr(vmware_module_utils.ssl, 'SSLContext')
    fake_ansible_module.params['validate_certs'] = True
    with pytest.raises(FailJsonException):
        vmware_module_utils.connect_to_api(fake_ansible_module)
    assert ssl_context.proto is None
    fake_ansible_module.fail_json.assert_called_once_with(msg=(
        'pyVim does not support changing verification mode with python '
        '< 2.7.9. Either update python or use validate_certs=false.'))
    assert not vmware_module_utils.connect.SmartConnect.called

    # Old Python with no SSLContext + validate_certs=False
    vmware_module_utils.connect.reset_mock()
    ssl_context = mock.Mock()
    ssl_context.proto = None
    monkeypatch.delattr(vmware_module_utils.ssl, 'SSLContext', raising=False)
    fake_ansible_module.params['validate_certs'] = False
    vmware_module_utils.connect_to_api(fake_ansible_module)
    assert ssl_context.proto is None
    vmware_module_utils.connect.SmartConnect.assert_called_once_with(
        host='esxi1',
        port=443,
        pwd='Esxi@123$%',
        user='Administrator@vsphere.local')
