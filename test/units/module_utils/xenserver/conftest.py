# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import sys
import importlib
import os
import json
import pytest

from .FakeAnsibleModule import FakeAnsibleModule
from ansible.module_utils import six
from mock import MagicMock


@pytest.fixture
def fake_ansible_module(request):
    """Returns fake AnsibleModule with fake module params."""
    if hasattr(request, 'param'):
        return FakeAnsibleModule(request.param)
    else:
        params = {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "validate_certs": True,
        }

        return FakeAnsibleModule(params)


@pytest.fixture(autouse=True)
def XenAPI():
    """Imports and returns fake XenAPI module."""

    # Import of fake XenAPI module is wrapped by fixture so that it does not
    # affect other unit tests which could potentialy also use XenAPI module.

    # First we use importlib.import_module() to import the module and assign
    # it to a local symbol.
    fake_xenapi = importlib.import_module('units.module_utils.xenserver.FakeXenAPI')

    # Now we populate Python module cache with imported fake module using the
    # original module name (XenAPI). That way, any 'import XenAPI' statement
    # will just load already imported fake module from the cache.
    sys.modules['XenAPI'] = fake_xenapi

    return fake_xenapi


@pytest.fixture(autouse=True)
def xenserver(XenAPI):
    """Imports and returns xenserver module util."""

    # Since we are wrapping fake XenAPI module inside a fixture, all modules
    # that depend on it have to be imported inside a test function. To make
    # this easier to handle and remove some code repetition, we wrap the import
    # of xenserver module util with a fixture.
    from ansible.module_utils import xenserver

    return xenserver


@pytest.fixture
def mock_xenapi_failure(XenAPI, mocker):
    """
    Returns mock object that raises XenAPI.Failure on any XenAPI
    method call.
    """
    fake_error_msg = "Fake XAPI method call error!"

    # We need to use our MagicMock based class that passes side_effect to its
    # children because calls to xenapi methods can generate an arbitrary
    # hierarchy of mock objects. Any such object when called should use the
    # same side_effect as its parent mock object.
    class MagicMockSideEffect(MagicMock):
        def _get_child_mock(self, **kw):
            child_mock = super(MagicMockSideEffect, self)._get_child_mock(**kw)
            child_mock.side_effect = self.side_effect
            return child_mock

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', new=MagicMockSideEffect(), create=True)
    mocked_xenapi.side_effect = XenAPI.Failure(fake_error_msg)

    return mocked_xenapi, fake_error_msg


@pytest.fixture
def fixture_data_from_file(request):
    """Loads fixture data from files."""
    if not hasattr(request, 'param'):
        return {}

    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    fixture_data = {}

    if isinstance(request.param, six.string_types):
        request.param = [request.param]

    for fixture_name in request.param:
        path = os.path.join(fixture_path, fixture_name)

        with open(path) as f:
            data = f.read()

        try:
            data = json.loads(data)
        except Exception:
            pass

        fixture_data[fixture_name] = data

    return fixture_data
