# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import collection
from ansible.galaxy.dependency_resolution.dataclasses import Requirement
from ansible.module_utils._text import to_native


def path_exists(path):
    if to_native(path) == '/root/.ansible/collections/ansible_collections/sandwiches/ham':
        return False
    elif to_native(path) == '/usr/share/ansible/collections/ansible_collections/sandwiches/reuben':
        return False
    elif to_native(path) == 'nope':
        return False
    else:
        return True


def isdir(path):
    if to_native(path) == 'nope':
        return False
    else:
        return True


def cliargs(collections_paths=None, collection_name=None):
    if collections_paths is None:
        collections_paths = ['~/root/.ansible/collections', '/usr/share/ansible/collections']

    context.CLIARGS._store = {
        'collections_path': collections_paths,
        'collection': collection_name,
        'type': 'collection',
        'output_format': 'human'
    }


@pytest.fixture
def mock_collection_objects(mocker):
    mocker.patch('ansible.cli.galaxy.GalaxyCLI._resolve_path', side_effect=['/root/.ansible/collections', '/usr/share/ansible/collections'])
    mocker.patch('ansible.cli.galaxy.validate_collection_path',
                 side_effect=['/root/.ansible/collections/ansible_collections', '/usr/share/ansible/collections/ansible_collections'])

    collection_args_1 = (
        (
            'sandwiches.pbj',
            '1.5.0',
            None,
            'dir',
        ),
        (
            'sandwiches.reuben',
            '2.5.0',
            None,
            'dir',
        ),
    )

    collection_args_2 = (
        (
            'sandwiches.pbj',
            '1.0.0',
            None,
            'dir',
        ),
        (
            'sandwiches.ham',
            '1.0.0',
            None,
            'dir',
        ),
    )

    collections_path_1 = [Requirement(*cargs) for cargs in collection_args_1]
    collections_path_2 = [Requirement(*cargs) for cargs in collection_args_2]

    mocker.patch('ansible.cli.galaxy.find_existing_collections', side_effect=[collections_path_1, collections_path_2])


@pytest.fixture
def mock_from_path(mocker):
    def _from_path(collection_name='pbj'):
        collection_args = {
            'sandwiches.pbj': (
                (
                    'sandwiches.pbj',
                    '1.5.0',
                    None,
                    'dir',
                ),
                (
                    'sandwiches.pbj',
                    '1.0.0',
                    None,
                    'dir',
                ),
            ),
            'sandwiches.ham': (
                (
                    'sandwiches.ham',
                    '1.0.0',
                    None,
                    'dir',
                ),
            ),
        }

        from_path_objects = [Requirement(*args) for args in collection_args[collection_name]]
        mocker.patch('ansible.cli.galaxy.Requirement.from_dir_path_as_unknown', side_effect=from_path_objects)

    return _from_path


def test_execute_list_collection_all(mocker, capsys, mock_collection_objects, tmp_path_factory):
    """Test listing all collections from multiple paths"""

    cliargs()

    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 12
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection        Version'
    assert out_lines[3] == '----------------- -------'
    assert out_lines[4] == 'sandwiches.pbj    1.5.0  '
    assert out_lines[5] == 'sandwiches.reuben 2.5.0  '
    assert out_lines[6] == ''
    assert out_lines[7] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[8] == 'Collection     Version'
    assert out_lines[9] == '-------------- -------'
    assert out_lines[10] == 'sandwiches.ham 1.0.0  '
    assert out_lines[11] == 'sandwiches.pbj 1.0.0  '


def test_execute_list_collection_specific(mocker, capsys, mock_collection_objects, mock_from_path, tmp_path_factory):
    """Test listing a specific collection"""

    collection_name = 'sandwiches.ham'
    mock_from_path(collection_name)

    cliargs(collection_name=collection_name)
    mocker.patch('os.path.exists', path_exists)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('ansible.galaxy.collection.validate_collection_name', collection_name)
    mocker.patch('ansible.cli.galaxy._get_collection_widths', return_value=(14, 5))

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', collection_name])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 5
    assert out_lines[0] == ''
    assert out_lines[1] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection     Version'
    assert out_lines[3] == '-------------- -------'
    assert out_lines[4] == 'sandwiches.ham 1.0.0  '


def test_execute_list_collection_specific_duplicate(mocker, capsys, mock_collection_objects, mock_from_path, tmp_path_factory):
    """Test listing a specific collection that exists at multiple paths"""

    collection_name = 'sandwiches.pbj'
    mock_from_path(collection_name)

    cliargs(collection_name=collection_name)
    mocker.patch('os.path.exists', path_exists)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('ansible.galaxy.collection.validate_collection_name', collection_name)

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', collection_name])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 10
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection     Version'
    assert out_lines[3] == '-------------- -------'
    assert out_lines[4] == 'sandwiches.pbj 1.5.0  '
    assert out_lines[5] == ''
    assert out_lines[6] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[7] == 'Collection     Version'
    assert out_lines[8] == '-------------- -------'
    assert out_lines[9] == 'sandwiches.pbj 1.0.0  '


def test_execute_list_collection_specific_invalid_fqcn(mocker, tmp_path_factory):
    """Test an invalid fully qualified collection name (FQCN)"""

    collection_name = 'no.good.name'

    cliargs(collection_name=collection_name)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', collection_name])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    with pytest.raises(AnsibleError, match='Invalid collection name'):
        gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)


def test_execute_list_collection_no_valid_paths(mocker, capsys, tmp_path_factory):
    """Test listing collections when no valid paths are given"""

    cliargs()

    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('ansible.utils.color.ANSIBLE_COLOR', False)
    mocker.patch('ansible.cli.galaxy.display.columns', 79)
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])

    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)

    with pytest.raises(AnsibleOptionsError, match=r'None of the provided paths were usable.'):
        gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()

    assert '[WARNING]: - the configured path' in err
    assert 'exists, but it\nis not a directory.' in err


def test_execute_list_collection_one_invalid_path(mocker, capsys, mock_collection_objects, tmp_path_factory):
    """Test listing all collections when one invalid path is given"""

    cliargs()
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', isdir)
    mocker.patch('ansible.cli.galaxy.GalaxyCLI._resolve_path', side_effect=['/root/.ansible/collections', 'nope'])
    mocker.patch('ansible.utils.color.ANSIBLE_COLOR', False)

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', '-p', 'nope'])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection        Version'
    assert out_lines[3] == '----------------- -------'
    assert out_lines[4] == 'sandwiches.pbj    1.5.0  '
    # Only a partial test of the output

    assert err == '[WARNING]: - the configured path nope, exists, but it is not a directory.\n'
