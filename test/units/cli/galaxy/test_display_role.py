# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.cli.galaxy import _display_role


def test_display_role(mocker, capsys):
    mocked_galaxy_role = mocker.Mock(install_info=None)
    mocked_galaxy_role.name = 'testrole'
    _display_role(mocked_galaxy_role)
    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == '- testrole, (unknown version)'


def test_display_role_known_version(mocker, capsys):
    mocked_galaxy_role = mocker.Mock(install_info={'version': '1.0.0'})
    mocked_galaxy_role.name = 'testrole'
    _display_role(mocked_galaxy_role)
    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == '- testrole, 1.0.0'
