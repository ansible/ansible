# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import sys
import importlib
import pytest

from .common import load_fixture, load_xenapi_db
from .FakeAnsibleModule import FakeAnsibleModule


@pytest.fixture
def fake_ansible_module(request):
    """Returns fake AnsibleModule with fake module parameters."""

    # Base module parameters.
    params = {
        "hostname": "some-host",
        "username": "some-user",
        "password": "some-pwd",
        "validate_certs": True,
    }

    # If additional module parameters are passed, update base
    # parameters with additional parameters.
    if hasattr(request, 'param'):
        params.update(request.param)

    return FakeAnsibleModule(params)


# This fixture is required for all test functions, hence autouse=True.
@pytest.fixture(autouse=True)
def XenAPI():
    """Imports and returns fake XenAPI module."""

    # Import of fake XenAPI module is wrapped by fixture so that it does not
    # affect other unit tests which could potentialy also use XenAPI module.

    # First we use importlib.import_module() to import the module and assign
    # it to a local symbol.
    fake_xenapi = importlib.import_module('units.modules.cloud.xenserver.FakeXenAPI')

    # Now we populate Python module cache with imported fake module using the
    # original module name (XenAPI). That way, any 'import XenAPI' statement
    # will just load already imported fake module from the cache.
    sys.modules['XenAPI'] = fake_xenapi

    return fake_xenapi


@pytest.fixture
def fake_xenapi_db(request, mocker, XenAPI):
    """
    Populates fake XenAPI DB by loading sample data from file. FakeXenAPI
    then mocks a number of XenAPI methods that act (get or set values)
    on that data.
    """
    if hasattr(request, 'param'):
        fake_xenapi_db_data = load_xenapi_db(request.param)
    else:
        fake_xenapi_db_data = load_xenapi_db()

    mocker.patch('XenAPI._XENAPI_DB', fake_xenapi_db_data)

    return fake_xenapi_db_data


@pytest.fixture
def fake_xenapi_db_vm(mocker, XenAPI):
    """Populates fake XenAPI DB with VM data from ansible-test-vm-db.json."""
    fake_xenapi_db_data = load_xenapi_db('ansible-test-vm-db.json')

    mocker.patch('XenAPI._XENAPI_DB', fake_xenapi_db_data)

    return fake_xenapi_db_data


@pytest.fixture
def fake_vm_facts(request):
    """Loads fake VM facts from file."""
    return load_fixture("vm-facts/%s" % request.param)


@pytest.fixture
def fake_vm_changes(request):
    """Loads fake VM changes from file."""
    return load_fixture("vm-changes/%s" % request.param)


# Since we are wrapping fake XenAPI module inside a fixture, all modules
# that depend on it have to also be imported inside a test function. To make
# things easier to handle and remove some code duplication, we wrap the import
# of particular xenserver_* module with a fixture. Starting here are such
# fixtures, one per module.

@pytest.fixture
def xenserver_guest(XenAPI):
    """Imports and returns xenserver_guest module."""
    from ansible.modules.cloud.xenserver import xenserver_guest

    return xenserver_guest


@pytest.fixture
def xenserver_guest_info(XenAPI):
    """Imports and returns xenserver_guest_info module."""
    from ansible.modules.cloud.xenserver import xenserver_guest_info

    return xenserver_guest_info


@pytest.fixture
def xenserver_guest_powerstate(XenAPI):
    """Imports and returns xenserver_guest_powerstate module."""
    from ansible.modules.cloud.xenserver import xenserver_guest_powerstate

    return xenserver_guest_powerstate
