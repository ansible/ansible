# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import pytest
import re
import tarfile
import tempfile
import time
import uuid

from io import BytesIO, StringIO
from units.compat.mock import MagicMock

import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError
from ansible.galaxy import collection
from ansible.module_utils._text import to_bytes, to_native, to_text
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
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    namespace = 'ansible_namespace'
    collection = 'collection'
    skeleton = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'collection_skeleton')

    galaxy_args = ['ansible-galaxy', 'collection', 'init', '%s.%s' % (namespace, collection),
                   '-c', '--init-path', test_dir, '--collection-skeleton', skeleton]
    GalaxyCLI(args=galaxy_args).run()
    collection_dir = os.path.join(test_dir, namespace, collection)
    output_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Output'))

    return collection_dir, output_dir


@pytest.fixture()
def publish_artifact(monkeypatch, tmp_path_factory):
    mock_open = MagicMock()
    monkeypatch.setattr(collection, 'open_url', mock_open)

    mock_uuid = MagicMock()
    mock_uuid.return_value.hex = 'uuid'
    monkeypatch.setattr(uuid, 'uuid4', mock_uuid)

    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    input_file = to_text(tmp_path / 'collection.tar.gz')

    with tarfile.open(input_file, 'w:gz') as tfile:
        b_io = BytesIO(b"\x00\x01\x02\x03")
        tar_info = tarfile.TarInfo('test')
        tar_info.size = 4
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    return input_file, mock_open


@pytest.fixture()
def requirements_file(request, tmp_path_factory):
    content = request.param

    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Requirements'))
    requirements_file = os.path.join(test_dir, 'requirements.yml')

    if content:
        with open(requirements_file, 'wb') as req_obj:
            req_obj.write(to_bytes(content))

    yield requirements_file


@pytest.fixture()
def galaxy_yml(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    b_galaxy_yml = os.path.join(b_test_dir, b'galaxy.yml')
    with open(b_galaxy_yml, 'wb') as galaxy_obj:
        galaxy_obj.write(to_bytes(request.param))

    yield b_galaxy_yml


def test_build_collection_no_galaxy_yaml():
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection galaxy.yml path '%s/galaxy.yml' does not exist." % fake_path)

    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(fake_path, 'output', False)


def test_build_existing_output_file(collection_input):
    input_dir, output_dir = collection_input

    existing_output_dir = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    os.makedirs(existing_output_dir)

    expected = "The output collection artifact '%s' already exists, but is a directory - aborting" \
               % to_native(existing_output_dir)
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(input_dir, output_dir, False)


def test_build_existing_output_without_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    expected = "The file '%s' already exists. You can use --force to re-create the collection artifact." \
               % to_native(existing_output)
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


@pytest.mark.parametrize('galaxy_yml', [b'namespace: value: broken'], indirect=True)
def test_invalid_yaml_galaxy_file(galaxy_yml):
    expected = to_native(b"Failed to parse the galaxy.yml at '%s' with the following error:" % galaxy_yml)

    with pytest.raises(AnsibleError, match=expected):
        collection._get_galaxy_yml(galaxy_yml)


@pytest.mark.parametrize('galaxy_yml', [b'namespace: test_namespace'], indirect=True)
def test_missing_required_galaxy_key(galaxy_yml):
    expected = "The collection galaxy.yml at '%s' is missing the following mandatory keys: authors, name, " \
               "readme, version" % to_native(galaxy_yml)

    with pytest.raises(AnsibleError, match=expected):
        collection._get_galaxy_yml(galaxy_yml)


@pytest.mark.parametrize('galaxy_yml', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
invalid: value"""], indirect=True)
def test_warning_extra_keys(galaxy_yml, monkeypatch):
    display_mock = MagicMock()
    monkeypatch.setattr(Display, 'warning', display_mock)

    collection._get_galaxy_yml(galaxy_yml)

    assert display_mock.call_count == 1
    assert display_mock.call_args[0][0] == "Found unknown keys in collection galaxy.yml at '%s': invalid"\
        % to_text(galaxy_yml)


@pytest.mark.parametrize('galaxy_yml', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md"""], indirect=True)
def test_defaults_galaxy_yml(galaxy_yml):
    actual = collection._get_galaxy_yml(galaxy_yml)

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


@pytest.mark.parametrize('galaxy_yml', [(b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
license: MIT"""), (b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
license:
- MIT""")], indirect=True)
def test_galaxy_yml_list_value(galaxy_yml):
    actual = collection._get_galaxy_yml(galaxy_yml)
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

    actual = collection._build_files_manifest(to_bytes(input_dir))

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

    actual = collection._build_files_manifest(to_bytes(input_dir))
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

    actual = collection._build_files_manifest(to_bytes(input_dir))

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

    with tarfile.open(output_artifact, mode='r') as actual:
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
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection path specified '%s' does not exist." % fake_path)

    with pytest.raises(AnsibleError, match=expected):
        collection.publish_collection(fake_path, None, None, False, True)


def test_publish_not_a_tarball():
    expected = "The collection path specified '{0}' is not a tarball, use 'ansible-galaxy collection build' to " \
               "create a proper release artifact."

    with tempfile.NamedTemporaryFile(prefix=u'ÅÑŚÌβŁÈ') as temp_file:
        temp_file.write(b"\x00")
        temp_file.flush()
        with pytest.raises(AnsibleError, match=expected.format(to_native(temp_file.name))):
            collection.publish_collection(temp_file.name, None, None, False, True)


def test_publish_no_wait(publish_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = publish_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v2/import/1234'
    server = 'https://galaxy.com'

    mock_open.return_value = StringIO(u'{"task":"%s"}' % fake_import_uri)
    expected_form, expected_content_type = collection._get_mime_data(to_bytes(artifact_path))

    collection.publish_collection(artifact_path, server, 'key', False, False)

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.com/api/v2/collections/'
    assert mock_open.mock_calls[0][2]['data'] == expected_form
    assert mock_open.mock_calls[0][2]['method'] == 'POST'
    assert mock_open.mock_calls[0][2]['validate_certs'] is True
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[0][2]['headers']['Content-length'] == len(expected_form)
    assert mock_open.mock_calls[0][2]['headers']['Content-type'] == expected_content_type

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Publishing collection artifact '%s' to %s" % (artifact_path, server)
    assert mock_display.mock_calls[1][1][0] == \
        "Collection has been pushed to the Galaxy server, not waiting until import has completed due to --no-wait " \
        "being set. Import task results can be found at %s" % fake_import_uri


def test_publish_dont_validate_cert(publish_artifact):
    artifact_path, mock_open = publish_artifact

    mock_open.return_value = StringIO(u'{"task":"https://galaxy.server.com/api/v2/import/1234"}')

    collection.publish_collection(artifact_path, 'https://galaxy.server.com', 'key', True, False)

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][2]['validate_certs'] is False


def test_publish_failure(publish_artifact):
    artifact_path, mock_open = publish_artifact

    mock_open.side_effect = urllib_error.HTTPError('https://galaxy.server.com', 500, 'msg', {}, StringIO())

    expected = 'Error when publishing collection (HTTP Code: 500, Message: Unknown error returned by Galaxy ' \
               'server. Code: Unknown)'
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection.publish_collection(artifact_path, 'https://galaxy.server.com', 'key', False, True)


def test_publish_failure_with_json_info(publish_artifact):
    artifact_path, mock_open = publish_artifact

    return_content = StringIO(u'{"message":"Galaxy error message","code":"GWE002"}')
    mock_open.side_effect = urllib_error.HTTPError('https://galaxy.server.com', 503, 'msg', {}, return_content)

    expected = 'Error when publishing collection (HTTP Code: 503, Message: Galaxy error message Code: GWE002)'
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection.publish_collection(artifact_path, 'https://galaxy.server.com', 'key', False, True)


def test_publish_with_wait(publish_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    fake_import_uri = 'https://galaxy-server/api/v2/import/1234'
    server = 'https://galaxy.server.com'

    artifact_path, mock_open = publish_artifact

    mock_open.side_effect = (
        StringIO(u'{"task":"%s"}' % fake_import_uri),
        StringIO(u'{"finished_at":"some_time","state":"success"}')
    )

    collection.publish_collection(artifact_path, server, 'key', False, True)

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[1][1][0] == fake_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[1][2]['validate_certs'] is True
    assert mock_open.mock_calls[1][2]['method'] == 'GET'

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Publishing collection artifact '%s' to %s" % (artifact_path, server)
    assert mock_display.mock_calls[1][1][0] == 'Collection has been successfully published to the Galaxy server'

    assert mock_vvv.call_count == 2
    assert mock_vvv.mock_calls[0][1][0] == 'Collection has been pushed to the Galaxy server %s' % server
    assert mock_vvv.mock_calls[1][1][0] == 'Waiting until galaxy import task %s has completed' % fake_import_uri


def test_publish_with_wait_timeout(publish_artifact, monkeypatch):
    monkeypatch.setattr(time, 'sleep', MagicMock())

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    fake_import_uri = 'https://galaxy-server/api/v2/import/1234'
    server = 'https://galaxy.server.com'

    artifact_path, mock_open = publish_artifact

    mock_open.side_effect = (
        StringIO(u'{"task":"%s"}' % fake_import_uri),
        StringIO(u'{"finished_at":null}'),
        StringIO(u'{"finished_at":"some_time","state":"success"}')
    )

    collection.publish_collection(artifact_path, server, 'key', True, True)

    assert mock_open.call_count == 3
    assert mock_open.mock_calls[1][1][0] == fake_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[1][2]['validate_certs'] is False
    assert mock_open.mock_calls[1][2]['method'] == 'GET'
    assert mock_open.mock_calls[2][1][0] == fake_import_uri
    assert mock_open.mock_calls[2][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[2][2]['validate_certs'] is False
    assert mock_open.mock_calls[2][2]['method'] == 'GET'

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Publishing collection artifact '%s' to %s" % (artifact_path, server)
    assert mock_display.mock_calls[1][1][0] == 'Collection has been successfully published to the Galaxy server'

    assert mock_vvv.call_count == 3
    assert mock_vvv.mock_calls[0][1][0] == 'Collection has been pushed to the Galaxy server %s' % server
    assert mock_vvv.mock_calls[1][1][0] == 'Waiting until galaxy import task %s has completed' % fake_import_uri
    assert mock_vvv.mock_calls[2][1][0] == \
        'Galaxy import process has a status of waiting, wait 2 seconds before trying again'


def test_publish_with_wait_and_failure(publish_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    mock_warn = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warn)

    mock_err = MagicMock()
    monkeypatch.setattr(Display, 'error', mock_err)

    fake_import_uri = 'https://galaxy-server/api/v2/import/1234'
    server = 'https://galaxy.server.com'

    artifact_path, mock_open = publish_artifact

    import_stat = {
        'finished_at': 'some_time',
        'state': 'failed',
        'error': {
            'code': 'GW001',
            'description': 'Because I said so!',

        },
        'messages': [
            {
                'level': 'error',
                'message': 'Some error',
            },
            {
                'level': 'warning',
                'message': 'Some warning',
            },
            {
                'level': 'info',
                'message': 'Some info',
            },
        ],
    }

    mock_open.side_effect = (
        StringIO(u'{"task":"%s"}' % fake_import_uri),
        StringIO(to_text(json.dumps(import_stat)))
    )

    expected = 'Galaxy import process failed: Because I said so! (Code: GW001)'
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection.publish_collection(artifact_path, server, 'key', True, True)

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[1][1][0] == fake_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[1][2]['validate_certs'] is False
    assert mock_open.mock_calls[1][2]['method'] == 'GET'

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == "Publishing collection artifact '%s' to %s" % (artifact_path, server)

    assert mock_vvv.call_count == 3
    assert mock_vvv.mock_calls[0][1][0] == 'Collection has been pushed to the Galaxy server %s' % server
    assert mock_vvv.mock_calls[1][1][0] == 'Waiting until galaxy import task %s has completed' % fake_import_uri
    assert mock_vvv.mock_calls[2][1][0] == 'Galaxy import message: info - Some info'

    assert mock_warn.call_count == 1
    assert mock_warn.mock_calls[0][1][0] == 'Galaxy import warning message: Some warning'

    assert mock_err.call_count == 1
    assert mock_err.mock_calls[0][1][0] == 'Galaxy import error message: Some error'


def test_publish_with_wait_and_failure_and_no_error(publish_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    mock_warn = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warn)

    mock_err = MagicMock()
    monkeypatch.setattr(Display, 'error', mock_err)

    fake_import_uri = 'https://galaxy-server/api/v2/import/1234'
    server = 'https://galaxy.server.com'

    artifact_path, mock_open = publish_artifact

    import_stat = {
        'finished_at': 'some_time',
        'state': 'failed',
        'error': {},
        'messages': [
            {
                'level': 'error',
                'message': 'Some error',
            },
            {
                'level': 'warning',
                'message': 'Some warning',
            },
            {
                'level': 'info',
                'message': 'Some info',
            },
        ],
    }

    mock_open.side_effect = (
        StringIO(u'{"task":"%s"}' % fake_import_uri),
        StringIO(to_text(json.dumps(import_stat)))
    )

    expected = 'Galaxy import process failed: Unknown error, see %s for more details (Code: UNKNOWN)' % fake_import_uri
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection.publish_collection(artifact_path, server, 'key', True, True)

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[1][1][0] == fake_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == 'Token key'
    assert mock_open.mock_calls[1][2]['validate_certs'] is False
    assert mock_open.mock_calls[1][2]['method'] == 'GET'

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == "Publishing collection artifact '%s' to %s" % (artifact_path, server)

    assert mock_vvv.call_count == 3
    assert mock_vvv.mock_calls[0][1][0] == 'Collection has been pushed to the Galaxy server %s' % server
    assert mock_vvv.mock_calls[1][1][0] == 'Waiting until galaxy import task %s has completed' % fake_import_uri
    assert mock_vvv.mock_calls[2][1][0] == 'Galaxy import message: info - Some info'

    assert mock_warn.call_count == 1
    assert mock_warn.mock_calls[0][1][0] == 'Galaxy import warning message: Some warning'

    assert mock_err.call_count == 1
    assert mock_err.mock_calls[0][1][0] == 'Galaxy import error message: Some error'


@pytest.mark.parametrize('requirements_file', [None], indirect=True)
def test_parse_requirements_file_that_doesnt_exist(requirements_file):
    expected = "The requirements file '%s' does not exist." % to_native(requirements_file)
    with pytest.raises(AnsibleError, match=expected):
        collection.parse_collections_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', ['not a valid yml file: hi: world'], indirect=True)
def test_parse_requirements_file_that_isnt_yaml(requirements_file):
    expected = "Failed to parse the collection requirements yml at '%s' with the following error" \
               % to_native(requirements_file)
    with pytest.raises(AnsibleError, match=expected):
        collection.parse_collections_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', [('''
# Older role based requirements.yml
- galaxy.role
- anotherrole
'''), ('''
# Doesn't have collections key
roles:
- galaxy.role
- anotherole
''')], indirect=True)
def test_parse_requirements_in_invalid_format(requirements_file):
    expected = "Expecting collections requirements file to be a dict with the key collections that contains a list " \
               "of collections to install."
    with pytest.raises(AnsibleError, match=expected):
        collection.parse_collections_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', ['''
collections:
- version: 1.0.0
'''], indirect=True)
def test_parse_requirements_without_mandatory_name_key(requirements_file):
    expected = "Collections requirement entry should contain the key name."
    with pytest.raises(AnsibleError, match=expected):
        collection.parse_collections_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', [('''
collections:
- namespace.collection1
- namespace.collection2
'''), ('''
collections:
- name: namespace.collection1
- name: namespace.collection2
''')], indirect=True)
def test_parse_requirements(requirements_file):
    expected = [('namespace.collection1', '*', None), ('namespace.collection2', '*', None)]
    actual = collection.parse_collections_requirements_file(requirements_file)

    assert actual == expected


@pytest.mark.parametrize('requirements_file', ['''
collections:
- name: namespace.collection1
  version: ">=1.0.0,<=2.0.0"
  source: https://galaxy-dev.ansible.com
- namespace.collection2'''], indirect=True)
def test_parse_requirements_with_extra_info(requirements_file):
    expected = [('namespace.collection1', '>=1.0.0,<=2.0.0', 'https://galaxy-dev.ansible.com'),
                ('namespace.collection2', '*', None)]
    actual = collection.parse_collections_requirements_file(requirements_file)

    assert actual == expected
