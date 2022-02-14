# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible import context
from ansible.galaxy import api, Galaxy
from ansible.galaxy.role import GalaxyRole

from ansible.cli.galaxy import _marshall_role


test_role_name = "test.role"
test_role_version = "0.0.1"


def test_marshall_role(galaxy_server):
    role = GalaxyRole(Galaxy(), galaxy_server, test_role_name)
    role._install_info = {"version": test_role_version}
    result = _marshall_role(role)
    assert result["name"] == test_role_name
    assert result["version"] == test_role_version


def test_marshall_role_no_install_info(galaxy_server):
    """Existing behaviour ignores the `version` kwarg"""
    role = GalaxyRole(Galaxy(), galaxy_server, test_role_name, version=test_role_version)
    result = _marshall_role(role)
    assert result["name"] == test_role_name
    assert result["version"] is None


def test_marshall_role_no_version(galaxy_server):
    role = GalaxyRole(Galaxy(), galaxy_server, test_role_name)
    result = _marshall_role(role)
    assert result["name"] == test_role_name
    assert result["version"] is None
