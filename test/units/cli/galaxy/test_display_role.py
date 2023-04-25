# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.cli.galaxy import _dump_roles_as_human


def test_display_role(mocker, capsys):
    marshalled_role = {'name': 'testrole', 'version': None}
    result = _dump_roles_as_human({'roles': [marshalled_role]})
    assert result == (
        "# roles\n"
        "- testrole, (unknown version)"
    )


def test_display_role_known_version(mocker, capsys):
    marshalled_role = {'name': 'testrole', 'version': '1.0.0'}
    result = _dump_roles_as_human({'roles': [marshalled_role]})
    assert result == (
        "# roles\n"
        "- testrole, 1.0.0"
    )
