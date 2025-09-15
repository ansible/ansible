# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import os
import pytest
import re
import tarfile
import tempfile
import uuid

from hashlib import sha256
from io import BytesIO
from unittest.mock import MagicMock, mock_open, patch

import ansible.constants as C
from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.config import manager
from ansible.errors import AnsibleError
from ansible.galaxy import api, collection, token
from ansible.module_utils.common.sentinel import Sentinel
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.common.file import S_IRWU_RG_RO
import builtins
from ansible.utils import context_objects as co
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash_s


@pytest.fixture(autouse=True)
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture
def collection_path_suffix(request):
    """Return test collection path suffix or the default."""
    return getattr(request, 'param', 'test-ÅÑŚÌβŁÈ Collections Input')


@pytest.fixture
def collection_input(tmp_path_factory, collection_path_suffix):
    """Create a collection skeleton directory for build tests."""
    test_dir = to_text(tmp_path_factory.mktemp(collection_path_suffix))

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
    """ Creates a temp collection artifact and mocked open_url instance for publishing tests """
    mock_open = MagicMock()
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    mock_uuid = MagicMock()
    mock_uuid.return_value.hex = 'uuid'
    monkeypatch.setattr(uuid, 'uuid4', mock_uuid)

    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    input_file = to_text(tmp_path / 'collection.tar.gz')

    with tarfile.open(input_file, 'w:gz') as tfile:
        b_io = BytesIO(b"\x00\x01\x02\x03")
        tar_info = tarfile.TarInfo('test')
        tar_info.size = 4
        tar_info.mode = S_IRWU_RG_RO
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    return input_file, mock_open


@pytest.fixture()
def galaxy_yml_dir(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    b_galaxy_yml = os.path.join(b_test_dir, b'galaxy.yml')
    with open(b_galaxy_yml, 'wb') as galaxy_obj:
        galaxy_obj.write(to_bytes(request.param))

    yield b_test_dir


@pytest.fixture()
def tmp_tarfile(tmp_path_factory, manifest_info):
    """ Creates a temporary tar file for _extract_tar_file tests """
    filename = u'ÅÑŚÌβŁÈ'
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-%s Collections' % to_native(filename)))
    tar_file = os.path.join(temp_dir, to_bytes('%s.tar.gz' % filename))
    data = os.urandom(8)

    with tarfile.open(tar_file, 'w:gz') as tfile:
        b_io = BytesIO(data)
        tar_info = tarfile.TarInfo(filename)
        tar_info.size = len(data)
        tar_info.mode = S_IRWU_RG_RO
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

        b_data = to_bytes(json.dumps(manifest_info, indent=True), errors='surrogate_or_strict')
        b_io = BytesIO(b_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(b_data)
        tar_info.mode = S_IRWU_RG_RO
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


@pytest.mark.parametrize(
    'required_signature_count,valid',
    [
        ("1", True),
        ("+1", True),
        ("all", True),
        ("+all", True),
        ("-1", False),
        ("invalid", False),
        ("1.5", False),
        ("+", False),
    ]
)
def test_cli_options(required_signature_count, valid, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
        '--keyring',
        '~/.ansible/pubring.kbx',
        '--required-valid-signature-count',
        required_signature_count
    ]

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)

    if valid:
        galaxy_cli.run()
    else:
        with pytest.raises(SystemExit, match='2') as error:
            galaxy_cli.run()


@pytest.mark.parametrize(
    "config,server",
    [
        (
            # Options to create ini config
            {
                'url': 'https://galaxy.ansible.com',
                'validate_certs': 'False',
            },
            # Expected server attributes
            {
                'validate_certs': False,
            },
        ),
        (
            {
                'url': 'https://galaxy.ansible.com',
                'validate_certs': 'True',
            },
            {
                'validate_certs': True,
            },
        ),
    ],
)
def test_bool_type_server_config_options(config, server, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]

    config_lines = [
        "[galaxy]",
        "server_list=server1\n",
        "[galaxy_server.server1]",
        "url=%s" % config['url'],
        "validate_certs=%s\n" % config['validate_certs'],
    ]

    with tempfile.NamedTemporaryFile(suffix='.cfg') as tmp_file:
        tmp_file.write(
            to_bytes('\n'.join(config_lines))
        )
        tmp_file.flush()

        with patch.object(C, 'GALAXY_SERVER_LIST', ['server1']):
            with patch.object(C.config, '_config_file', tmp_file.name):
                C.config._parse_config_file()
                galaxy_cli = GalaxyCLI(args=cli_args)
                mock_execute_install = MagicMock()
                monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
                galaxy_cli.run()

    assert galaxy_cli.api_servers[0].name == 'server1'
    assert galaxy_cli.api_servers[0].validate_certs == server['validate_certs']


@pytest.mark.parametrize('global_ignore_certs', [True, False])
def test_validate_certs(global_ignore_certs, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]
    if global_ignore_certs:
        cli_args.append('--ignore-certs')

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert len(galaxy_cli.api_servers) == 1
    assert galaxy_cli.api_servers[0].validate_certs is not global_ignore_certs


@pytest.mark.parametrize(
    ["ignore_certs_cli", "ignore_certs_cfg", "expected_validate_certs"],
    [
        (None, None, True),
        (None, True, False),
        (None, False, True),
        (True, None, False),
        (True, True, False),
        (True, False, False),
    ]
)
def test_validate_certs_with_server_url(ignore_certs_cli, ignore_certs_cfg, expected_validate_certs, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
        '-s',
        'https://galaxy.ansible.com'
    ]
    if ignore_certs_cli:
        cli_args.append('--ignore-certs')
    if ignore_certs_cfg is not None:
        monkeypatch.setattr(C, 'GALAXY_IGNORE_CERTS', ignore_certs_cfg)

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert len(galaxy_cli.api_servers) == 1
    assert galaxy_cli.api_servers[0].validate_certs == expected_validate_certs


@pytest.mark.parametrize(
    ["ignore_certs_cli", "ignore_certs_cfg", "expected_server2_validate_certs", "expected_server3_validate_certs"],
    [
        (None, None, True, True),
        (None, True, True, False),
        (None, False, True, True),
        (True, None, False, False),
        (True, True, False, False),
        (True, False, False, False),
    ]
)
def test_validate_certs_server_config(ignore_certs_cfg, ignore_certs_cli, expected_server2_validate_certs, expected_server3_validate_certs, monkeypatch):
    server_names = ['server1', 'server2', 'server3']
    cfg_lines = [
        "[galaxy]",
        "server_list=server1,server2,server3",
        "[galaxy_server.server1]",
        "url=https://galaxy.ansible.com/api/",
        "validate_certs=False",
        "[galaxy_server.server2]",
        "url=https://galaxy.ansible.com/api/",
        "validate_certs=True",
        "[galaxy_server.server3]",
        "url=https://galaxy.ansible.com/api/",
    ]
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]
    if ignore_certs_cli:
        cli_args.append('--ignore-certs')
    if ignore_certs_cfg is not None:
        monkeypatch.setattr(C, 'GALAXY_IGNORE_CERTS', ignore_certs_cfg)

    monkeypatch.setattr(C, 'GALAXY_SERVER_LIST', server_names)

    with tempfile.NamedTemporaryFile(suffix='.cfg') as tmp_file:
        tmp_file.write(to_bytes('\n'.join(cfg_lines), errors='surrogate_or_strict'))
        tmp_file.flush()

        monkeypatch.setattr(C.config, '_config_file', tmp_file.name)
        C.config._parse_config_file()
        galaxy_cli = GalaxyCLI(args=cli_args)
        mock_execute_install = MagicMock()
        monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
        galaxy_cli.run()

    # (not) --ignore-certs > server's validate_certs > (not) GALAXY_IGNORE_CERTS > True
    assert galaxy_cli.api_servers[0].validate_certs is False
    assert galaxy_cli.api_servers[1].validate_certs is expected_server2_validate_certs
    assert galaxy_cli.api_servers[2].validate_certs is expected_server3_validate_certs


@pytest.mark.parametrize(
    ["timeout_cli", "timeout_cfg", "timeout_fallback", "expected_timeout"],
    [
        (None, None, None, 60),
        (None, None, 10, 10),
        (None, 20, 10, 20),
        (30, 20, 10, 30),
    ]
)
def test_timeout_server_config(timeout_cli, timeout_cfg, timeout_fallback, expected_timeout, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]
    if timeout_cli is not None:
        cli_args.extend(["--timeout", f"{timeout_cli}"])

    cfg_lines = ["[galaxy]", "server_list=server1"]
    if timeout_fallback is not None:
        cfg_lines.append(f"server_timeout={timeout_fallback}")

        # fix default in server config since C.GALAXY_SERVER_TIMEOUT was already evaluated
        server_additional = manager.GALAXY_SERVER_ADDITIONAL.copy()
        server_additional['timeout']['default'] = timeout_fallback
        monkeypatch.setattr(manager, 'GALAXY_SERVER_ADDITIONAL', server_additional)

    cfg_lines.extend(["[galaxy_server.server1]", "url=https://galaxy.ansible.com/api/"])
    if timeout_cfg is not None:
        cfg_lines.append(f"timeout={timeout_cfg}")

    monkeypatch.setattr(C, 'GALAXY_SERVER_LIST', ['server1'])

    with tempfile.NamedTemporaryFile(suffix='.cfg') as tmp_file:
        tmp_file.write(to_bytes('\n'.join(cfg_lines), errors='surrogate_or_strict'))
        tmp_file.flush()

        monkeypatch.setattr(C.config, '_config_file', tmp_file.name)
        C.config._parse_config_file()

        galaxy_cli = GalaxyCLI(args=cli_args)
        mock_execute_install = MagicMock()
        monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
        galaxy_cli.run()

    assert galaxy_cli.api_servers[0].timeout == expected_timeout


def test_build_collection_no_galaxy_yaml():
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection galaxy.yml path '%s/galaxy.yml' does not exist." % fake_path)

    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(fake_path, u'output', False)


def test_build_existing_output_file(collection_input):
    input_dir, output_dir = collection_input

    existing_output_dir = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    os.makedirs(existing_output_dir)

    expected = "The output collection artifact '%s' already exists, but is a directory - aborting" \
               % to_native(existing_output_dir)
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)


def test_build_existing_output_without_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    expected = "The file '%s' already exists. You can use --force to re-create the collection artifact." \
               % to_native(existing_output)
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)


@pytest.mark.parametrize(
    'collection_path_suffix',
    (
        'test-ÅÑŚÌβŁÈ Collections Input 1 with_slash/',
        'test-ÅÑŚÌβŁÈ Collections Input 2 no slash',
    ),
    indirect=('collection_path_suffix', ),
)
def test_build_existing_output_with_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), True)

    # Verify the file was replaced with an actual tar file
    assert tarfile.is_tarfile(existing_output)


def test_build_with_existing_files_and_manifest(collection_input):
    input_dir, output_dir = collection_input

    with open(os.path.join(input_dir, 'MANIFEST.json'), "wb") as fd:
        fd.write(b'{"collection_info": {"version": "6.6.6"}, "version": 1}')

    with open(os.path.join(input_dir, 'FILES.json'), "wb") as fd:
        fd.write(b'{"files": [], "format": 1}')

    with open(os.path.join(input_dir, "plugins", "MANIFEST.json"), "wb") as fd:
        fd.write(b"test data that should be in build")

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        manifest_file = [m for m in members if m.path == "MANIFEST.json"][0]
        manifest_file_obj = actual.extractfile(manifest_file.name)
        manifest_file_text = manifest_file_obj.read()
        manifest_file_obj.close()
        assert manifest_file_text != b'{"collection_info": {"version": "6.6.6"}, "version": 1}'

        json_file = [m for m in members if m.path == "MANIFEST.json"][0]
        json_file_obj = actual.extractfile(json_file.name)
        json_file_text = json_file_obj.read()
        json_file_obj.close()
        assert json_file_text != b'{"files": [], "format": 1}'

        sub_manifest_file = [m for m in members if m.path == "plugins/MANIFEST.json"][0]
        sub_manifest_file_obj = actual.extractfile(sub_manifest_file.name)
        sub_manifest_file_text = sub_manifest_file_obj.read()
        sub_manifest_file_obj.close()
        assert sub_manifest_file_text == b"test data that should be in build"


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: value: broken'], indirect=True)
def test_invalid_yaml_galaxy_file(galaxy_yml_dir):
    galaxy_file = os.path.join(galaxy_yml_dir, b'galaxy.yml')
    expected = to_native(b"Failed to parse the galaxy.yml at '%s' with the following error:" % galaxy_file)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: test_namespace'], indirect=True)
def test_missing_required_galaxy_key(galaxy_yml_dir):
    galaxy_file = os.path.join(galaxy_yml_dir, b'galaxy.yml')
    expected = "The collection galaxy.yml at '%s' is missing the following mandatory keys: authors, name, " \
               "readme, version" % to_native(galaxy_file)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: test_namespace'], indirect=True)
def test_galaxy_yaml_no_mandatory_keys(galaxy_yml_dir):
    expected = "The collection galaxy.yml at '%s/galaxy.yml' is missing the " \
               "following mandatory keys: authors, name, readme, version" % to_native(galaxy_yml_dir)

    with pytest.raises(ValueError, match=expected):
        assert collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir, require_build_metadata=False) == expected


@pytest.mark.parametrize('galaxy_yml_dir', [b'My life story is so very interesting'], indirect=True)
def test_galaxy_yaml_no_mandatory_keys_bad_yaml(galaxy_yml_dir):
    expected = "The collection galaxy.yml at '%s/galaxy.yml' is incorrectly formatted." % to_native(galaxy_yml_dir)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
invalid: value"""], indirect=True)
def test_warning_extra_keys(galaxy_yml_dir, monkeypatch):
    display_mock = MagicMock()
    monkeypatch.setattr(Display, 'warning', display_mock)

    collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)

    assert display_mock.call_count == 1
    assert display_mock.call_args[0][0] == "Found unknown keys in collection galaxy.yml at '%s/galaxy.yml': invalid"\
        % to_text(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md"""], indirect=True)
def test_defaults_galaxy_yml(galaxy_yml_dir):
    actual = collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)

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
    assert actual['license'] == []


@pytest.mark.parametrize('galaxy_yml_dir', [(b"""
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
def test_galaxy_yml_list_value(galaxy_yml_dir):
    actual = collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)
    assert actual['license'] == ['MIT']


def test_build_ignore_files_and_folders(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    git_folder = os.path.join(input_dir, '.git')
    retry_file = os.path.join(input_dir, 'ansible.retry')

    tests_folder = os.path.join(input_dir, 'tests', 'output')
    tests_output_file = os.path.join(tests_folder, 'result.txt')

    os.makedirs(git_folder)
    os.makedirs(tests_folder)

    with open(retry_file, 'w+') as ignore_file:
        ignore_file.write('random')
        ignore_file.flush()

    with open(tests_output_file, 'w+') as tests_file:
        tests_file.write('random')
        tests_file.flush()

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel, None)

    assert actual['format'] == 1
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] not in ['.git', 'ansible.retry', 'galaxy.yml', 'tests/output', 'tests/output/result.txt']

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s' for collection build" % to_text(retry_file),
        "Skipping '%s' for collection build" % to_text(git_folder),
        "Skipping '%s' for collection build" % to_text(tests_folder),
    ]
    assert mock_display.call_count == 4
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs
    assert mock_display.mock_calls[2][1][0] in expected_msgs
    assert mock_display.mock_calls[3][1][0] in expected_msgs


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

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel, None)
    assert actual['format'] == 1

    plugin_release_found = False
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] != 'namespace-collection-0.0.0.tar.gz'
        if manifest_entry['name'] == 'plugins/namespace-collection-0.0.0.tar.gz':
            plugin_release_found = True

    assert plugin_release_found

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s' for collection build" % to_text(release_file)
    ]
    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs


def test_build_ignore_patterns(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection',
                                              ['*.md', 'plugins/action', 'playbooks/*.j2'],
                                              Sentinel, None)
    assert actual['format'] == 1

    expected_missing = [
        'README.md',
        'docs/My Collection.md',
        'plugins/action',
        'playbooks/templates/test.conf.j2',
        'playbooks/templates/subfolder/test.conf.j2',
    ]

    # Files or dirs that are close to a match but are not, make sure they are present
    expected_present = [
        'docs',
        'roles/common/templates/test.conf.j2',
        'roles/common/templates/subfolder/test.conf.j2',
    ]

    actual_files = [e['name'] for e in actual['files']]
    for m in expected_missing:
        assert m not in actual_files

    for p in expected_present:
        assert p in actual_files

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s/README.md' for collection build" % to_text(input_dir),
        "Skipping '%s/docs/My Collection.md' for collection build" % to_text(input_dir),
        "Skipping '%s/plugins/action' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/test.conf.j2' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/subfolder/test.conf.j2' for collection build" % to_text(input_dir),
    ]
    assert mock_display.call_count == len(expected_msgs)
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs
    assert mock_display.mock_calls[2][1][0] in expected_msgs
    assert mock_display.mock_calls[3][1][0] in expected_msgs
    assert mock_display.mock_calls[4][1][0] in expected_msgs
    assert mock_display.mock_calls[5][1][0] in expected_msgs


def test_build_ignore_symlink_target_outside_collection(collection_input, monkeypatch):
    input_dir, outside_dir = collection_input

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_display)

    link_path = os.path.join(input_dir, 'plugins', 'connection')
    os.symlink(outside_dir, link_path)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel, None)
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

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel, None)

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

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        linked_folder = [m for m in members if m.path == 'playbooks/roles/linked'][0]
        assert linked_folder.type == tarfile.SYMTYPE
        assert linked_folder.linkname == '../../roles/linked'

        linked_file = [m for m in members if m.path == 'docs/README.md'][0]
        assert linked_file.type == tarfile.SYMTYPE
        assert linked_file.linkname == '../README.md'

        linked_file_obj = actual.extractfile(linked_file.name)
        actual_file = secure_hash_s(linked_file_obj.read())
        linked_file_obj.close()

        assert actual_file == '08f24200b9fbe18903e7a50930c9d0df0b8d7da3'  # shasum test/units/cli/test_data/collection_skeleton/README.md


def test_publish_no_wait(galaxy_server, collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = collection_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v3/import/1234'

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
    fake_import_uri = 'https://galaxy.server.com/api/v3/import/1234'

    mock_publish = MagicMock()
    mock_publish.return_value = fake_import_uri
    monkeypatch.setattr(galaxy_server, 'publish_collection', mock_publish)

    mock_wait = MagicMock()
    monkeypatch.setattr(galaxy_server, 'wait_import_task', mock_wait)

    collection.publish_collection(artifact_path, galaxy_server, True, 0)

    assert mock_publish.call_count == 1
    assert mock_publish.mock_calls[0][1][0] == artifact_path

    assert mock_wait.call_count == 1
    assert mock_wait.mock_calls[0][1][0] == fake_import_uri

    assert mock_display.mock_calls[0][1][0] == "Collection has been published to the Galaxy server test_server %s" \
        % galaxy_server.api_server


def test_download_file(tmp_path_factory, monkeypatch):
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))

    data = b"\x00\x01\x02\x03"
    sha256_hash = sha256()
    sha256_hash.update(data)

    mock_open = MagicMock()
    mock_open.return_value = BytesIO(data)
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    expected = temp_dir
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
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

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
        tar_info.mode = S_IRWU_RG_RO
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = re.escape("Cannot extract tar entry '%s' as it will be placed outside the collection directory"
                         % to_native(tar_filename))
    with tarfile.open(tar_file, 'r') as tfile:
        with pytest.raises(AnsibleError, match=expected):
            collection._extract_tar_file(tfile, tar_filename, os.path.join(temp_dir, to_bytes(filename)), temp_dir)


def test_require_one_of_collections_requirements_with_both():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', 'namespace.collection', '-r', 'requirements.yml'])

    with pytest.raises(AnsibleError) as req_err:
        cli._require_one_of_collections_requirements(('namespace.collection',), 'requirements.yml')

    with pytest.raises(AnsibleError) as cli_err:
        cli.run()

    assert req_err.value.message == cli_err.value.message == 'The positional collection_name arg and --requirements-file are mutually exclusive.'


def test_require_one_of_collections_requirements_with_neither():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify'])

    with pytest.raises(AnsibleError) as req_err:
        cli._require_one_of_collections_requirements((), '')

    with pytest.raises(AnsibleError) as cli_err:
        cli.run()

    assert req_err.value.message == cli_err.value.message == 'You must specify a collection name or a requirements file.'


def test_require_one_of_collections_requirements_with_collections():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', 'namespace1.collection1', 'namespace2.collection1:1.0.0'])
    collections = ('namespace1.collection1', 'namespace2.collection1:1.0.0',)

    requirements = cli._require_one_of_collections_requirements(collections, '')['collections']

    req_tuples = [('%s.%s' % (req.namespace, req.name), req.ver, req.src, req.type,) for req in requirements]
    assert req_tuples == [('namespace1.collection1', '*', None, 'galaxy'), ('namespace2.collection1', '1.0.0', None, 'galaxy')]


@patch('ansible.cli.galaxy.GalaxyCLI._parse_requirements_file')
def test_require_one_of_collections_requirements_with_requirements(mock_parse_requirements_file, galaxy_server):
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', '-r', 'requirements.yml', 'namespace.collection'])
    mock_parse_requirements_file.return_value = {'collections': [('namespace.collection', '1.0.5', galaxy_server)]}
    requirements = cli._require_one_of_collections_requirements((), 'requirements.yml')['collections']

    assert mock_parse_requirements_file.call_count == 1
    assert requirements == [('namespace.collection', '1.0.5', galaxy_server)]


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify', spec=True)
def test_call_GalaxyCLI(execute_verify):
    galaxy_args = ['ansible-galaxy', 'collection', 'verify', 'namespace.collection']

    GalaxyCLI(args=galaxy_args).run()

    assert execute_verify.call_count == 1


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify')
def test_call_GalaxyCLI_with_implicit_role(execute_verify):
    galaxy_args = ['ansible-galaxy', 'verify', 'namespace.implicit_role']

    with pytest.raises(SystemExit):
        GalaxyCLI(args=galaxy_args).run()

    assert not execute_verify.called


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify')
def test_call_GalaxyCLI_with_role(execute_verify):
    galaxy_args = ['ansible-galaxy', 'role', 'verify', 'namespace.role']

    with pytest.raises(SystemExit):
        GalaxyCLI(args=galaxy_args).run()

    assert not execute_verify.called


@patch('ansible.cli.galaxy.verify_collections', spec=True)
def test_execute_verify_with_defaults(mock_verify_collections):
    galaxy_args = ['ansible-galaxy', 'collection', 'verify', 'namespace.collection:1.0.4']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_verify_collections.call_count == 1

    print("Call args {0}".format(mock_verify_collections.call_args[0]))
    requirements, search_paths, galaxy_apis, ignore_errors = mock_verify_collections.call_args[0]

    assert [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type) for r in requirements] == [('namespace.collection', '1.0.4', None, 'galaxy')]
    for install_path in search_paths:
        assert install_path.endswith('ansible_collections')
    assert galaxy_apis[0].api_server == 'https://galaxy.ansible.com'
    assert ignore_errors is False


@patch('ansible.cli.galaxy.verify_collections', spec=True)
def test_execute_verify(mock_verify_collections):
    GalaxyCLI(args=[
        'ansible-galaxy', 'collection', 'verify', 'namespace.collection:1.0.4', '--ignore-certs',
        '-p', '~/.ansible', '--ignore-errors', '--server', 'http://galaxy-dev.com',
    ]).run()

    assert mock_verify_collections.call_count == 1

    requirements, search_paths, galaxy_apis, ignore_errors = mock_verify_collections.call_args[0]

    assert [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type) for r in requirements] == [('namespace.collection', '1.0.4', None, 'galaxy')]
    for install_path in search_paths:
        assert install_path.endswith('ansible_collections')
    assert galaxy_apis[0].api_server == 'http://galaxy-dev.com'
    assert ignore_errors is True


def test_verify_file_hash_deleted_file(manifest_info):
    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=False)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', digest, error_queue)

            mock_isfile.assert_called_once()

    assert len(error_queue) == 1
    assert error_queue[0].installed is None
    assert error_queue[0].expected == digest


def test_verify_file_hash_matching_hash(manifest_info):

    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=True)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', digest, error_queue)

            mock_isfile.assert_called_once()

    assert error_queue == []


def test_verify_file_hash_mismatching_hash(manifest_info):

    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()
    different_digest = 'not_{0}'.format(digest)

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=True)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', different_digest, error_queue)

            mock_isfile.assert_called_once()

    assert len(error_queue) == 1
    assert error_queue[0].installed == digest
    assert error_queue[0].expected == different_digest


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


def test_get_tar_file_hash(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    assert checksum == collection._get_tar_file_hash(tfile.name, filename)


def test_get_json_from_tar_file(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    assert 'MANIFEST.json' in tfile.getnames()

    data = collection._get_json_from_tar_file(tfile.name, 'MANIFEST.json')

    assert isinstance(data, dict)
