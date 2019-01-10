# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import sys
import importlib
import pytest

sys.modules['XenAPI'] = importlib.import_module('units.module_utils.xenserver.FakeXenAPI')

from .FakeAnsibleModule import FakeAnsibleModule, ExitJsonException, FailJsonException
from .common import *
from ansible.module_utils.xenserver import *


def test_xenserverobject_xenapi_lib_detection(mocker, fake_ansible_module):
    """Tests XenAPI lib detection code."""
    mocker.patch('ansible.module_utils.xenserver.HAS_XENAPI', new=False)

    with pytest.raises(FailJsonException) as exc_info:
        XenServerObject(fake_ansible_module)

    assert exc_info.value.kwargs['msg'] == "XenAPI.py required for this module! Please download XenServer SDK and copy XenAPI.py to your site-packages."


def test_xenserverobject_xenapi_failure(mock_xenapi_failure, fake_ansible_module):
    """Tests catching of XenAPI failures."""
    with pytest.raises(FailJsonException) as exc_info:
        XenServerObject(fake_ansible_module)

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: %s" % mock_xenapi_failure[1]


def test_xenserverobject(mocker, fake_ansible_module):
    """Tests successful creation of XenServerObject."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_refs['pool']],
        "pool.get_default_SR.return_value": fake_xenapi_refs['sr'],
        "session.get_this_host.return_value": fake_xenapi_refs['host'],
        "host.get_software_version.return_value": {"product_version_text_short": "7.2"},
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    xso = XenServerObject(fake_ansible_module)

    assert xso.pool_ref == fake_xenapi_refs['pool']
    assert xso.xenserver_version == ['7', '2']
