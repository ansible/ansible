# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import sys
import importlib
import pytest


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


@pytest.fixture
def xenserver_guest_facts(XenAPI):
    """Imports and returns xenserver_guest_facts module."""

    # Since we are wrapping fake XenAPI module inside a fixture, all modules
    # that depend on it have to be imported inside a test function. To make
    # this easier to handle and remove some code repetition, we wrap the import
    # of xenserver_guest_facts module with a fixture.
    from ansible.modules.cloud.xenserver import xenserver_guest_facts

    return xenserver_guest_facts
