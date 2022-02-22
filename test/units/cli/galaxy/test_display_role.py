# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible.galaxy import Galaxy
from ansible.galaxy.role import GalaxyRole

from ansible.cli.galaxy import _dump_roles_as_human, _marshall_role


test_role_name = "test.role"
test_role_version = "0.0.1"
test_role_path = "test/path"


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


def test_dump_role_as_human_known_version():
    marshalled_role = {"name": test_role_name, "version": test_role_version}
    result = _dump_roles_as_human({test_role_path: [marshalled_role]})

    assert result == (
        "# test/path\n"
        "- test.role, 0.0.1"
    )


def test_dump_role_as_human_unknown_version():
    marshalled_role = {"name": test_role_name, "version": None}
    result = _dump_roles_as_human({test_role_path: [marshalled_role]})

    assert result == (
        "# test/path\n"
        "- test.role, (unknown version)"
    )


def test_dump_role_as_human_multiples():
    marshalled = {
        (test_role_path + '0'): [
            {"name": test_role_name + '00', "version": test_role_version},
            {"name": test_role_name + '01', "version": test_role_version},
        ],
        (test_role_path + '1'): [
            {"name": test_role_name + '10', "version": test_role_version},
            {"name": test_role_name + '11', "version": test_role_version},
        ]
    }

    result = _dump_roles_as_human(marshalled)

    assert result == (
        "# test/path0\n"
        "- test.role00, 0.0.1\n"
        "- test.role01, 0.0.1\n"
        "# test/path1\n"
        "- test.role10, 0.0.1\n"
        "- test.role11, 0.0.1"
    )
