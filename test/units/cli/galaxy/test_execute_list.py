# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import pytest

from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.galaxy.collection import CollectionRequirement
from ansible.module_utils._text import to_native


def path_exists(path):
    if to_native(path) == 'nope':
        return False
    else:
        return os.path.isdir(path)


def cliargs(collections_paths=None, collection_name=None):
    if collections_paths is None:
        collections_paths = ['~/root/.ansible/collections', '/usr/share/ansible/collections']

    context.CLIARGS._store = {
        'collections_path': collections_paths,
        'collection': collection_name,
    }


@pytest.fixture
def mock_collection_objects(mocker):
    mocker.patch('ansible.cli.galaxy.GalaxyCLI._resolve_path', side_effect=['/root/.ansible/collections', '/usr/share/ansible/collections'])
    mocker.patch('ansible.cli.galaxy.validate_collection_path',
                 side_effect=['/root/.ansible/collections/ansible_collections', '/usr/share/ansible/collections/ansible_collections'])

    collection_args = (
        (
            'sandwiches',
            'ham',
            b'/usr/share/ansible/collections/ansible_collections/sandwiches/ham',
            mocker.Mock(),
            ['1.0.0'],
            '1.0.0',
            False,
        ),
        (
            'sandwiches',
            'pbj',
            b'/usr/share/ansible/collections/ansible_collections/sandwiches/pbj',
            mocker.Mock(),
            ['1.0.0', '1.5.0'],
            '1.0.0',
            False,
        ),
        (
            'sandwiches',
            'pbj',
            b'/root/.ansible/collections/ansible_collections/sandwiches/pbj',
            mocker.Mock(),
            ['1.0.0', '1.5.0'],
            '1.5.0',
            False,
        ),
        (
            'sandwiches',
            'reuben',
            b'/root/.ansible/collections/ansible_collections/sandwiches/pbj',
            mocker.Mock(),
            ['1.0.0', '2.5.0'],
            '2.5.0',
            False,
        ),
    )

    mocker.patch('ansible.cli.galaxy.find_existing_collections', return_value=[CollectionRequirement(*cargs) for cargs in collection_args])
    mocker.patch('ansible.galaxy.collection.CollectionRequirement.from_path', return_value=CollectionRequirement(*collection_args[0]))


def test_execute_list_role_called(mocker):
    # Make sure the correct method is called for a role
    gc = GalaxyCLI(['ansible-galaxy', 'role', 'list'])
    context.CLIARGS._store = {'type': 'role'}
    execute_list_role_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_role', side_effect=AttributeError('raised intentionally'))
    execute_list_collection_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_collection', side_effect=AttributeError('raised intentionally'))
    with pytest.raises(AttributeError):
        gc.execute_list()

    assert execute_list_role_mock.call_count == 1
    assert execute_list_collection_mock.call_count == 0


def test_execute_list_collection_called(mocker):
    # Make sure the correct method is called for a collection
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    context.CLIARGS._store = {'type': 'collection'}
    execute_list_role_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_role', side_effect=AttributeError('raised intentionally'))
    execute_list_collection_mock = mocker.patch('ansible.cli.galaxy.GalaxyCLI.execute_list_collection', side_effect=AttributeError('raised intentionally'))
    with pytest.raises(AttributeError):
        gc.execute_list()

    assert execute_list_role_mock.call_count == 0
    assert execute_list_collection_mock.call_count == 1


def test_execute_list_collection_all(mocker, capsys, mock_collection_objects):
    cliargs()
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    gc.execute_list_collection()

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 16
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection        Version'
    assert out_lines[3] == '----------------- -------'
    assert out_lines[4] == 'sandwiches.ham    1.0.0'
    assert out_lines[5] == 'sandwiches.pbj    1.0.0'
    assert out_lines[6] == 'sandwiches.pbj    1.5.0'
    assert out_lines[7] == 'sandwiches.reuben 2.5.0'
    assert out_lines[8] == ''
    assert out_lines[9] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[10] == 'Collection        Version'
    assert out_lines[11] == '----------------- -------'
    assert out_lines[12] == 'sandwiches.ham    1.0.0'
    assert out_lines[13] == 'sandwiches.pbj    1.0.0'
    assert out_lines[14] == 'sandwiches.pbj    1.5.0'
    assert out_lines[15] == 'sandwiches.reuben 2.5.0'


def test_execute_list_collection_specific(mocker, capsys, mock_collection_objects):
    collection_name = 'sandwiches.ham'

    cliargs(collection_name=collection_name)
    mocker.patch('os.path.exists', side_effect=path_exists)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('ansible.galaxy.collection.validate_collection_name', collection_name)
    mocker.patch('ansible.cli.galaxy.to_bytes', side_effect=[b'~/root/.ansible/collections/ansible_collections/sandwiches/ham', b'nope'])
    mocker.patch('ansible.cli.galaxy._get_collection_widths', return_value=(14, 5))

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', 'sandwiches.ham'])
    gc.execute_list_collection()

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 5
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection     Version'
    assert out_lines[3] == '-------------- -------'
    assert out_lines[4] == 'sandwiches.ham 1.0.0'


def test_execute_list_collection_specific_invalid_fqcn(capsys, mock_collection_objects):
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', 'bad'])


def test_execute_list_collection_invalid_path(capsys, mock_collection_objects):
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', '-p', 'nope'])
