# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible import context
from ansible.cli.galaxy import GalaxyCLI


def test_execute_list_role_called(mocker):
    """Make sure the correct method is called for a role"""

    gc = GalaxyCLI(['ansible-galaxy', 'role', 'list'])
    context.CLIARGS._store = {'type': 'role'}
    execute_list_role_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_role', side_effect=AttributeError('raised intentionally'))
    execute_list_collection_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_collection', side_effect=AttributeError('raised intentionally'))
    with pytest.raises(AttributeError):
        gc.execute_list()

    assert execute_list_role_mock.call_count == 1
    assert execute_list_collection_mock.call_count == 0


def test_execute_list_collection_called(mocker):
    """Make sure the correct method is called for a collection"""

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    context.CLIARGS._store = {'type': 'collection'}
    execute_list_role_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_role', side_effect=AttributeError('raised intentionally'))
    execute_list_collection_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_collection', side_effect=AttributeError('raised intentionally'))
    with pytest.raises(AttributeError):
        gc.execute_list()

    assert execute_list_role_mock.call_count == 0
    assert execute_list_collection_mock.call_count == 1
