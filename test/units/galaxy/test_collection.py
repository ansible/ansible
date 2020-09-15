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
import uuid

from hashlib import sha256
from io import BytesIO
from units.compat.mock import MagicMock, mock_open, patch

from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError
from ansible.galaxy import api, collection, token
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six.moves import builtins
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
    ''' Creates a collection skeleton directory for build tests '''
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
def collection_artifact(monkeypatch, tmp_path_factory):
    ''' Creates a temp collection artifact and mocked open_url instance for publishing tests '''
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
def galaxy_yml(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    b_galaxy_yml = os.path.join(b_test_dir, b'galaxy.yml')
    with open(b_galaxy_yml, 'wb') as galaxy_obj:
        galaxy_obj.write(to_bytes(request.param))

    yield b_galaxy_yml


@pytest.fixture()
def tmp_tarfile(tmp_path_factory):
    ''' Creates a temporary tar file for _extract_tar_file tests '''
    filename = u'ÅÑŚÌβŁÈ'
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-%s Collections' % to_native(filename)))
    tar_file = os.path.join(temp_dir, to_bytes('%s.tar.gz' % filename))
    data = os.urandom(8)

    with tarfile.open(tar_file, 'w:gz') as tfile:
        b_io = BytesIO(data)
        tar_info = tarfile.TarInfo(filename)
        tar_info.size = len(data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    sha256_hash = sha256()
    sha256_hash.update(data)

    with tarfile.open(tar_file, 'r') as tfile:
        yield temp_dir, tfile, filename, sha256_hash.hexdigest()


@pytest.fixture()
def galaxy_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(None, 'test_server', 'https://galaxy.ansible.com',
                               token=token.GalaxyToken(token='key'))
    return galaxy_api


@pytest.fixture()
def manifest_template():
    def get_manifest_info(namespace='ansible_namespace', name='collection', version='0.1.0'):
        return {
            "collection_info": {
                "namespace": namespace,
                "name": name,
                "version": version,
                "authors": [
                    "shertel"
                ],
                "readme": "README.md",
                "tags": [
                    "test",
                    "collection"
                ],
                "description": "Test",
                "license": [
                    "MIT"
                ],
                "license_file": None,
                "dependencies": {},
                "repository": "https://github.com/{0}/{1}".format(namespace, name),
                "documentation": None,
                "homepage": None,
                "issues": None
            },
            "file_manifest_file": {
                "name": "FILES.json",
                "ftype": "file",
                "chksum_type": "sha256",
                "chksum_sha256": "files_manifest_checksum",
                "format": 1
            },
            "format": 1
        }

    return get_manifest_info


@pytest.fixture()
def manifest_info(manifest_template):
    return manifest_template()


@pytest.fixture()
def manifest(manifest_info):
    b_data = to_bytes(json.dumps(manifest_info))

    with patch.object(builtins, 'open', mock_open(read_data=b_data)) as m:
        with open('MANIFEST.json', mode='rb') as fake_file:
            yield fake_file, sha256(b_data).hexdigest()


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

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection')

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


def test_build_ignore_older_release_in_root(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    # This is expected to be ignored because it is in the root collection dir.
    release_file = os.path.join(input_dir, 'namespace-collection-0.0.0.tar.gz')

    # This is not expected to be ignored because it is not in the root collection dir.
    fake_release_file = os.path.join(input_dir, 'plugins', 'namespace-collection-0.0.0.tar.gz')

    for filename in [release_file, fake_release_file]:
        with open(filename, 'w+') as file_obj:
            file_obj.write('random')
            file_obj.flush()

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection')
    assert actual['format'] == 1

    plugin_release_found = False
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] != 'namespace-collection-0.0.0.tar.gz'
        if manifest_entry['name'] == 'plugins/namespace-collection-0.0.0.tar.gz':
            plugin_release_found = True

    assert plugin_release_found

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == "Skipping '%s' for collection build" % to_text(release_file)


def test_build_ignore_symlink_target_outside_collection(collection_input, monkeypatch):
    input_dir, outside_dir = collection_input

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_display)

    link_path = os.path.join(input_dir, 'plugins', 'connection')
    os.symlink(outside_dir, link_path)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection')
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

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection')

    linked_entries = [e for e in actual['files'] if e['name'].startswith('playbooks/roles/linked')]
    assert len(linked_entries) == 1
    assert linked_entries[0]['name'] == 'playbooks/roles/linked'
    assert linked_entries[0]['ftype'] == 'dir'


def test_build_with_symlink_inside_collection(collection_input):
    input_dir, output_dir = collection_input

    os.makedirs(os.path.join(input_dir, 'playbooks', 'roles'))
    roles_link = os.path.join(input_dir, 'playbooks', 'roles', 'linked')
    file_link = os.path.join(input_dir, 'docs', 'README.md')

    roles_target = os.path.join(input_dir, 'roles', 'linked')
    roles_target_tasks = os.path.join(roles_target, 'tasks')
    os.makedirs(roles_target_tasks)
    with open(os.path.join(roles_target_tasks, 'main.yml'), 'w+') as tasks_main:
        tasks_main.write("---\n- hosts: localhost\n  tasks:\n  - ping:")
        tasks_main.flush()

    os.symlink(roles_target, roles_link)
    os.symlink(os.path.join(input_dir, 'README.md'), file_link)

    collection.build_collection(input_dir, output_dir, False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        linked_folder = next(m for m in members if m.path == 'playbooks/roles/linked')
        assert linked_folder.type == tarfile.SYMTYPE
        assert linked_folder.linkname == '../../roles/linked'

        linked_file = next(m for m in members if m.path == 'docs/README.md')
        assert linked_file.type == tarfile.SYMTYPE
        assert linked_file.linkname == '../README.md'

        linked_file_obj = actual.extractfile(linked_file.name)
        actual_file = secure_hash_s(linked_file_obj.read())
        linked_file_obj.close()

        assert actual_file == '63444bfc766154e1bc7557ef6280de20d03fcd81'


def test_publish_no_wait(galaxy_server, collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = collection_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v2/import/1234'

    mock_publish = MagicMock()
    mock_publish.return_value = fake_import_uri
    monkeypatch.setattr(galaxy_server, 'publish_collection', mock_publish)

    collection.publish_collection(artifact_path, galaxy_server, False, 0)

    assert mock_publish.call_count == 1
    assert mock_publish.mock_calls[0][1][0] == artifact_path

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == \
        "Collection has been pushed to the Galaxy server %s %s, not waiting until import has completed due to " \
        "--no-wait being set. Import task results can be found at %s" % (galaxy_server.name, galaxy_server.api_server,
                                                                         fake_import_uri)


def test_publish_with_wait(galaxy_server, collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = collection_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v2/import/1234'

    mock_publish = MagicMock()
    mock_publish.return_value = fake_import_uri
    monkeypatch.setattr(galaxy_server, 'publish_collection', mock_publish)

    mock_wait = MagicMock()
    monkeypatch.setattr(galaxy_server, 'wait_import_task', mock_wait)

    collection.publish_collection(artifact_path, galaxy_server, True, 0)

    assert mock_publish.call_count == 1
    assert mock_publish.mock_calls[0][1][0] == artifact_path

    assert mock_wait.call_count == 1
    assert mock_wait.mock_calls[0][1][0] == '1234'

    assert mock_display.mock_calls[0][1][0] == "Collection has been published to the Galaxy server test_server %s" \
        % galaxy_server.api_server


def test_find_existing_collections(tmp_path_factory, monkeypatch):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    collection1 = os.path.join(test_dir, 'namespace1', 'collection1')
    collection2 = os.path.join(test_dir, 'namespace2', 'collection2')
    fake_collection1 = os.path.join(test_dir, 'namespace3', 'collection3')
    fake_collection2 = os.path.join(test_dir, 'namespace4')
    os.makedirs(collection1)
    os.makedirs(collection2)
    os.makedirs(os.path.split(fake_collection1)[0])

    open(fake_collection1, 'wb+').close()
    open(fake_collection2, 'wb+').close()

    collection1_manifest = json.dumps({
        'collection_info': {
            'namespace': 'namespace1',
            'name': 'collection1',
            'version': '1.2.3',
            'authors': ['Jordan Borean'],
            'readme': 'README.md',
            'dependencies': {},
        },
        'format': 1,
    })
    with open(os.path.join(collection1, 'MANIFEST.json'), 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(collection1_manifest))

    mock_warning = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warning)

    actual = collection._find_existing_collections(test_dir)

    assert len(actual) == 2
    for actual_collection in actual:
        assert actual_collection.skip is True

        if str(actual_collection) == 'namespace1.collection1':
            assert actual_collection.namespace == 'namespace1'
            assert actual_collection.name == 'collection1'
            assert actual_collection.b_path == to_bytes(collection1)
            assert actual_collection.api is None
            assert actual_collection.versions == set(['1.2.3'])
            assert actual_collection.latest_version == '1.2.3'
            assert actual_collection.dependencies == {}
        else:
            assert actual_collection.namespace == 'namespace2'
            assert actual_collection.name == 'collection2'
            assert actual_collection.b_path == to_bytes(collection2)
            assert actual_collection.api is None
            assert actual_collection.versions == set(['*'])
            assert actual_collection.latest_version == '*'
            assert actual_collection.dependencies == {}

    assert mock_warning.call_count == 1
    assert mock_warning.mock_calls[0][1][0] == "Collection at '%s' does not have a MANIFEST.json file, cannot " \
                                               "detect version." % to_text(collection2)


def test_download_file(tmp_path_factory, monkeypatch):
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))

    data = b"\x00\x01\x02\x03"
    sha256_hash = sha256()
    sha256_hash.update(data)

    mock_open = MagicMock()
    mock_open.return_value = BytesIO(data)
    monkeypatch.setattr(collection, 'open_url', mock_open)

    expected = os.path.join(temp_dir, b'file')
    actual = collection._download_file('http://google.com/file', temp_dir, sha256_hash.hexdigest(), True)

    assert actual.startswith(expected)
    assert os.path.isfile(actual)
    with open(actual, 'rb') as file_obj:
        assert file_obj.read() == data

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'http://google.com/file'


def test_download_file_hash_mismatch(tmp_path_factory, monkeypatch):
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))

    data = b"\x00\x01\x02\x03"

    mock_open = MagicMock()
    mock_open.return_value = BytesIO(data)
    monkeypatch.setattr(collection, 'open_url', mock_open)

    expected = "Mismatch artifact hash with downloaded file"
    with pytest.raises(AnsibleError, match=expected):
        collection._download_file('http://google.com/file', temp_dir, 'bad', True)


def test_extract_tar_file_invalid_hash(tmp_tarfile):
    temp_dir, tfile, filename, dummy = tmp_tarfile

    expected = "Checksum mismatch for '%s' inside collection at '%s'" % (to_native(filename), to_native(tfile.name))
    with pytest.raises(AnsibleError, match=expected):
        collection._extract_tar_file(tfile, filename, temp_dir, temp_dir, "fakehash")


def test_extract_tar_file_missing_member(tmp_tarfile):
    temp_dir, tfile, dummy, dummy = tmp_tarfile

    expected = "Collection tar at '%s' does not contain the expected file 'missing'." % to_native(tfile.name)
    with pytest.raises(AnsibleError, match=expected):
        collection._extract_tar_file(tfile, 'missing', temp_dir, temp_dir)


def test_extract_tar_file_missing_parent_dir(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile
    output_dir = os.path.join(temp_dir, b'output')
    output_file = os.path.join(output_dir, to_bytes(filename))

    collection._extract_tar_file(tfile, filename, output_dir, temp_dir, checksum)
    os.path.isfile(output_file)


def test_extract_tar_file_outside_dir(tmp_path_factory):
    filename = u'ÅÑŚÌβŁÈ'
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-%s Collections' % to_native(filename)))
    tar_file = os.path.join(temp_dir, to_bytes('%s.tar.gz' % filename))
    data = os.urandom(8)

    tar_filename = '../%s.sh' % filename
    with tarfile.open(tar_file, 'w:gz') as tfile:
        b_io = BytesIO(data)
        tar_info = tarfile.TarInfo(tar_filename)
        tar_info.size = len(data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = re.escape("Cannot extract tar entry '%s' as it will be placed outside the collection directory"
                         % to_native(tar_filename))
    with tarfile.open(tar_file, 'r') as tfile:
        with pytest.raises(AnsibleError, match=expected):
            collection._extract_tar_file(tfile, tar_filename, os.path.join(temp_dir, to_bytes(filename)), temp_dir)


def test_consume_file(manifest):

    manifest_file, checksum = manifest
    assert checksum == collection._consume_file(manifest_file)


def test_consume_file_and_write_contents(manifest, manifest_info):

    manifest_file, checksum = manifest

    write_to = BytesIO()
    actual_hash = collection._consume_file(manifest_file, write_to)

    write_to.seek(0)
    assert to_bytes(json.dumps(manifest_info)) == write_to.read()
    assert actual_hash == checksum


def test_get_tar_file_member(tmp_tarfile):

    temp_dir, tfile, filename, checksum = tmp_tarfile

    with collection._get_tar_file_member(tfile, filename) as (tar_file_member, tar_file_obj):
        assert isinstance(tar_file_member, tarfile.TarInfo)
        assert isinstance(tar_file_obj, tarfile.ExFileObject)


def test_get_nonexistent_tar_file_member(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    file_does_not_exist = filename + 'nonexistent'

    with pytest.raises(AnsibleError) as err:
        collection._get_tar_file_member(tfile, file_does_not_exist)

    assert to_text(err.value.message) == "Collection tar at '%s' does not contain the expected file '%s'." % (to_text(tfile.name), file_does_not_exist)
