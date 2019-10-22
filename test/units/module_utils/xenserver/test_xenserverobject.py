# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from .FakeAnsibleModule import FakeAnsibleModule, ExitJsonException, FailJsonException
from .common import fake_xenapi_ref


def test_xenserverobject_xenapi_lib_detection(mocker, fake_ansible_module, xenserver):
    """Tests XenAPI lib detection code."""
    mocker.patch('ansible.module_utils.xenserver.HAS_XENAPI', new=False)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.XenServerObject(fake_ansible_module)

    assert 'Failed to import the required Python library (XenAPI) on' in exc_info.value.kwargs['msg']


def test_xenserverobject_xenapi_failure(mock_xenapi_failure, fake_ansible_module, xenserver):
    """Tests catching of XenAPI failures."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.XenServerObject(fake_ansible_module)

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: %s" % mock_xenapi_failure[1]


def test_xenserverobject(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests successful creation of XenServerObject."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
        "session.get_this_host.return_value": fake_xenapi_ref('host'),
        "host.get_software_version.return_value": {"product_version": "7.2.0"},
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    xso = xenserver.XenServerObject(fake_ansible_module)

    assert xso.pool_ref == fake_xenapi_ref('pool')
    assert xso.xenserver_version == [7, 2, 0]
