# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import ansible
import pytest

from distutils.version import LooseVersion

from ansible import context
from ansible.module_utils._text import to_native
from ansible.cli.galaxy import GalaxyCLI


class FakeCollection:
    def __init__(self, namespace, name, b_path, api, versions, requirement, force, parent=None, metadata=None,
                 files=None, skip=False):

        self.namespace = namespace
        self.name = name
        self.b_path = b_path
        self.api = api
        self.versions = set(versions)
        self.force = force
        self.skip = skip
        self.required_by = []
        self._metadata = metadata
        self._files = files

    def __str__(self):
        return to_native("%s.%s" % (self.namespace, self.name))

    def __unicode__(self):
        return u"%s.%s" % (self.namespace, self.name)

    @property
    def latest_version(self):
        try:
            return max([v for v in self.versions if v != '*'], key=LooseVersion)
        except ValueError:  # ValueError: max() arg is an empty sequence
            return '*'


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


def test_execute_list_collection_all(mocker):
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    context.CLIARGS._store = {
        'collections_path': ['~/root/.ansible/collections', '/usr/share/ansible/collections'],
        'collection': None,
    }

    mocker.patch('ansible.cli.galaxy.GalaxyCLI._resolve_path', return_value='/usr/share/ansible/collections')
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('ansible.cli.galaxy.validate_collection_path', return_value='/usr/share/ansible/collections/ansible_collections')

    collection_args = (
        (
            'sandwiches',
            'ham',
            b'/usr/share/ansible/collections/ansible_collections/sandwiches/ham',
            mocker.Mock(),
            ['1.0.0'],
            {},
            False,
        ),
        (
            'sandwiches',
            'pbj',
            b'/usr/share/ansible/collections/ansible_collections/sandwiches/pbj',
            mocker.Mock(),
            ['1.5.0'],
            {},
            False,
        ),
    )
    mocker.patch('ansible.cli.galaxy.find_existing_collections', return_value=[FakeCollection(*cargs) for cargs in collection_args])

    mock_display = mocker.patch.object(ansible.utils.display.Display, 'display', return_value=None)
    mock_display_vvv = mocker.patch.object(ansible.utils.display.Display, 'vvv', return_value=None)
    gc.execute_list_collection()

    header_lines = mock_display.call_args_list[0][0][0].splitlines()

    assert mock_display.call_count == 6
    assert header_lines[0] == ''
    assert header_lines[1] == '# /usr/share/ansible/collections/ansible_collections'
    assert header_lines[2] == 'Collection     Version'
    assert header_lines[3] == '-------------- -------'
    assert mock_display.call_args_list[1] == (('sandwiches.ham 1.0.0',),)
    assert mock_display.call_args_list[2] == (('sandwiches.pbj 1.5.0',),)

    assert mock_display_vvv.call_count == 2
    assert mock_display_vvv.call_args == (('Searching /usr/share/ansible/collections/ansible_collections for collections',),)


def test_execute_list_collection_specific():
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', 'sandwiches.ham'])


def test_execute_list_collection_specific_invalid_fqcn():
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', 'bad'])


def test_execute_list_collection_invalid_path():
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', '-p', 'nope'])
