# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest
import tarfile
import tempfile

from units.compat.mock import MagicMock

from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError
from ansible.galaxy import collection
from ansible.module_utils._text import to_text
from ansible.utils import context_objects as co
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash_s


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture()
def collection_input(tmp_path_factory):
    test_dir = str(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    namespace = 'ansible_namespace'
    collection = 'collection'
    skeleton = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'collection_skeleton')

    galaxy_args = ['ansible-galaxy', 'collection', 'init', '%s.%s' % (namespace, collection),
                   '-c', '--init-path', test_dir, '--collection-skeleton', skeleton]
    GalaxyCLI(args=galaxy_args).run()
    collection_dir = os.path.join(test_dir, namespace, collection)
    output_dir = str(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Output'))

    return collection_dir, output_dir


def test_build_collection_no_galaxy_yaml():
    expected = "The collection galaxy.yml path '/fake/path/galaxy.yml' does not exist."

    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection('/fake/path', 'output', False)


def test_build_existing_output_file(collection_input):
    input_dir, output_dir = collection_input

    existing_output_dir = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    os.makedirs(existing_output_dir)

    expected = "The output collection artifact '%s' already exists, but is a directory - aborting" \
               % existing_output_dir
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(input_dir, output_dir, False)


def test_build_existing_output_without_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    expected = "The file '%s' already exists. You can use --force to re-create the collection artifact." \
               % existing_output
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(input_dir, output_dir, False)


def test_build_existing_output_with_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    collection.build_collection(input_dir, output_dir, True)

    # Verify the file was replaced with an actual tar file
    assert tarfile.is_tarfile(existing_output)


def test_invalid_yaml_galaxy_file():
    expected = "Failed to parse the galaxy.yml at '{0}' with the following error:"

    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: value: broken")
        galaxy_yml.flush()

        with pytest.raises(AnsibleError, match=expected.format(galaxy_yml.name)):
            collection._get_galaxy_yml(galaxy_yml.name)


def test_missing_required_galaxy_key():
    expected = "The collection galaxy.yml at '{0}' is missing the following mandatory keys: authors, name, readme, " \
               "version"

    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: test_namespace")
        galaxy_yml.flush()

        with pytest.raises(AnsibleError, match=expected.format(galaxy_yml.name)):
            collection._get_galaxy_yml(galaxy_yml.name)


def test_warning_extra_keys(monkeypatch):
    display_mock = MagicMock()
    monkeypatch.setattr(Display, 'warning', display_mock)

    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: namespace\nname: collection\nauthors: Jordan\nversion: 0.1.0\n"
                         b"readme: README.md\ninvalid: value")
        galaxy_yml.flush()

        collection._get_galaxy_yml(galaxy_yml.name)

    assert display_mock.call_count == 1
    assert display_mock.call_args[0][0] == \
        "Found unknown keys in collection galaxy.yml at '{0}': invalid".format(galaxy_yml.name)


def test_defaults_galaxy_yml():
    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: namespace\nname: collection\nauthors: Jordan\nversion: 0.1.0\nreadme: README.md")
        galaxy_yml.flush()

        actual = collection._get_galaxy_yml(galaxy_yml.name)

    assert sorted(list(actual.keys())) == [
        'authors', 'dependencies', 'description', 'documentation', 'homepage', 'issues', 'license_file', 'license_ids',
        'name', 'namespace', 'readme', 'repository', 'tags', 'version',
    ]

    assert actual['namespace'] == 'namespace'
    assert actual['name'] == 'collection'
    assert actual['authors'] == ['Jordan']
    assert actual['version'] == '0.1.0'
    assert actual['readme'] == 'README.md'
    assert actual['description'] is None
    assert actual['repository'] is None
    assert actual['documentation'] is None
    assert actual['homepage'] is None
    assert actual['issues'] is None
    assert actual['tags'] == []
    assert actual['dependencies'] == {}
    assert actual['license_ids'] == []


def test_galaxy_yml_list_value_as_str():
    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: namespace\nname: collection\nauthors: Jordan\nversion: 0.1.0\n"
                         b"readme: README.md\nlicense: MIT\n")
        galaxy_yml.flush()

        actual = collection._get_galaxy_yml(galaxy_yml.name)

    assert actual['license_ids'] == ['MIT']


def test_galaxy_yml_list_val_as_list():
    with tempfile.NamedTemporaryFile(suffix='-ÅÑŚÌβŁÈ galaxy.yml') as galaxy_yml:
        galaxy_yml.write(b"namespace: namespace\nname: collection\nauthors: Jordan\nversion: 0.1.0\n"
                         b"readme: README.md\nlicense:\n- MIT")
        galaxy_yml.flush()

        actual = collection._get_galaxy_yml(galaxy_yml.name)

    assert actual['license_ids'] == ['MIT']


def test_build_ignore_files_and_folders(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    git_folder = os.path.join(input_dir, '.git')
    retry_file = os.path.join(input_dir, 'ansible.retry')

    os.makedirs(git_folder)
    with open(retry_file, 'w+') as ignore_file:
        ignore_file.write('random')
        ignore_file.flush()

    actual = collection._build_files_manifest(input_dir)

    assert actual['format'] == 1
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] not in ['.git', 'ansible.retry', 'galaxy.yml']

    expected_msgs = [
        "Skipping '%s' for collection build" % to_text(retry_file),
        "Skipping '%s' for collection build" % to_text(git_folder),
    ]
    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs


def test_build_ignore_symlink_target_outside_collection(collection_input, monkeypatch):
    input_dir, outside_dir = collection_input

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_display)

    link_path = os.path.join(input_dir, 'plugins', 'connection')
    os.symlink(outside_dir, link_path)

    actual = collection._build_files_manifest(input_dir)
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] != 'plugins/connection'

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == "Skipping '%s' as it is a symbolic link to a directory outside " \
                                               "the collection" % to_text(link_path)


def test_build_copy_symlink_target_inside_collection(collection_input):
    input_dir = collection_input[0]

    os.makedirs(os.path.join(input_dir, 'playbooks', 'roles'))
    roles_link = os.path.join(input_dir, 'playbooks', 'roles', 'linked')

    roles_target = os.path.join(input_dir, 'roles', 'linked')
    roles_target_tasks = os.path.join(roles_target, 'tasks')
    os.makedirs(roles_target_tasks)
    with open(os.path.join(roles_target_tasks, 'main.yml'), 'w+') as tasks_main:
        tasks_main.write("---\n- hosts: localhost\n  tasks:\n  - ping:")
        tasks_main.flush()

    os.symlink(roles_target, roles_link)

    actual = collection._build_files_manifest(input_dir)

    linked_entries = [e for e in actual['files'] if e['name'].startswith('playbooks/roles/linked')]
    assert len(linked_entries) == 3
    assert linked_entries[0]['name'] == 'playbooks/roles/linked'
    assert linked_entries[0]['ftype'] == 'dir'
    assert linked_entries[1]['name'] == 'playbooks/roles/linked/tasks'
    assert linked_entries[1]['ftype'] == 'dir'
    assert linked_entries[2]['name'] == 'playbooks/roles/linked/tasks/main.yml'
    assert linked_entries[2]['ftype'] == 'file'
    assert linked_entries[2]['chksum_sha256'] == '9c97a1633c51796999284c62236b8d5462903664640079b80c37bf50080fcbc3'


def test_build_with_symlink_inside_collection(collection_input):
    input_dir, output_dir = collection_input

    os.makedirs(os.path.join(input_dir, 'playbooks', 'roles'))
    roles_link = os.path.join(input_dir, 'playbooks', 'roles', 'linked')

    roles_target = os.path.join(input_dir, 'roles', 'linked')
    roles_target_tasks = os.path.join(roles_target, 'tasks')
    os.makedirs(roles_target_tasks)
    with open(os.path.join(roles_target_tasks, 'main.yml'), 'w+') as tasks_main:
        tasks_main.write("---\n- hosts: localhost\n  tasks:\n  - ping:")
        tasks_main.flush()

    os.symlink(roles_target, roles_link)

    collection.build_collection(input_dir, output_dir, False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with collection._open_tarfile(output_artifact) as actual:
        members = actual.getmembers()

        linked_members = [m for m in members if m.path.startswith('playbooks/roles/linked/tasks')]
        assert len(linked_members) == 2
        assert linked_members[0].name == 'playbooks/roles/linked/tasks'
        assert linked_members[0].isdir()

        assert linked_members[1].name == 'playbooks/roles/linked/tasks/main.yml'
        assert linked_members[1].isreg()

        linked_task = actual.extractfile(linked_members[1].name)
        actual_task = secure_hash_s(linked_task.read())
        linked_task.close()

        assert actual_task == 'f4dcc52576b6c2cd8ac2832c52493881c4e54226'


def test_publish_missing_file():
    expected = "The collection path specified '/fake/path' does not exist."

    with pytest.raises(AnsibleError, match=expected):
        collection.publish_collection('/fake/path', None, None, False, True)


def test_publish_not_a_tarball():
    expected = "The collection path specified '{0}' is not a tarball, use 'ansible-galaxy collection build' to " \
               "create a proper release artifact."

    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(b"\x00")
        temp_file.flush()
        with pytest.raises(AnsibleError, match=expected.format(temp_file.name)):
            collection.publish_collection(temp_file.name, None, None, False, True)
