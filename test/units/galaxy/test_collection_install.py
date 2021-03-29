# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import json
import os
import pytest
import re
import shutil
import stat
import tarfile
import yaml

from io import BytesIO, StringIO
from units.compat.mock import MagicMock

import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError
from ansible.galaxy import collection, api, dependency_resolution
from ansible.galaxy.dependency_resolution.dataclasses import Candidate, Requirement
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils import context_objects as co
from ansible.utils.display import Display


class RequirementCandidates():
    def __init__(self):
        self.candidates = []

    def func_wrapper(self, func):
        def run(*args, **kwargs):
            self.candidates = func(*args, **kwargs)
            return self.candidates
        return run


def call_galaxy_cli(args):
    orig = co.GlobalCLIArgs._Singleton__instance
    co.GlobalCLIArgs._Singleton__instance = None
    try:
        GalaxyCLI(args=['ansible-galaxy', 'collection'] + args).run()
    finally:
        co.GlobalCLIArgs._Singleton__instance = orig


def artifact_json(namespace, name, version, dependencies, server):
    json_str = json.dumps({
        'artifact': {
            'filename': '%s-%s-%s.tar.gz' % (namespace, name, version),
            'sha256': '2d76f3b8c4bab1072848107fb3914c345f71a12a1722f25c08f5d3f51f4ab5fd',
            'size': 1234,
        },
        'download_url': '%s/download/%s-%s-%s.tar.gz' % (server, namespace, name, version),
        'metadata': {
            'namespace': namespace,
            'name': name,
            'dependencies': dependencies,
        },
        'version': version
    })
    return to_text(json_str)


def artifact_versions_json(namespace, name, versions, galaxy_api, available_api_versions=None):
    results = []
    available_api_versions = available_api_versions or {}
    api_version = 'v2'
    if 'v3' in available_api_versions:
        api_version = 'v3'
    for version in versions:
        results.append({
            'href': '%s/api/%s/%s/%s/versions/%s/' % (galaxy_api.api_server, api_version, namespace, name, version),
            'version': version,
        })

    if api_version == 'v2':
        json_str = json.dumps({
            'count': len(versions),
            'next': None,
            'previous': None,
            'results': results
        })

    if api_version == 'v3':
        response = {'meta': {'count': len(versions)},
                    'data': results,
                    'links': {'first': None,
                              'last': None,
                              'next': None,
                              'previous': None},
                    }
        json_str = json.dumps(response)
    return to_text(json_str)


def error_json(galaxy_api, errors_to_return=None, available_api_versions=None):
    errors_to_return = errors_to_return or []
    available_api_versions = available_api_versions or {}

    response = {}

    api_version = 'v2'
    if 'v3' in available_api_versions:
        api_version = 'v3'

    if api_version == 'v2':
        assert len(errors_to_return) <= 1
        if errors_to_return:
            response = errors_to_return[0]

    if api_version == 'v3':
        response['errors'] = errors_to_return

    json_str = json.dumps(response)
    return to_text(json_str)


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture()
def collection_artifact(request, tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    namespace = 'ansible_namespace'
    collection = 'collection'

    skeleton_path = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'collection_skeleton')
    collection_path = os.path.join(test_dir, namespace, collection)

    call_galaxy_cli(['init', '%s.%s' % (namespace, collection), '-c', '--init-path', test_dir,
                     '--collection-skeleton', skeleton_path])
    dependencies = getattr(request, 'param', None)
    if dependencies:
        galaxy_yml = os.path.join(collection_path, 'galaxy.yml')
        with open(galaxy_yml, 'rb+') as galaxy_obj:
            existing_yaml = yaml.safe_load(galaxy_obj)
            existing_yaml['dependencies'] = dependencies

            galaxy_obj.seek(0)
            galaxy_obj.write(to_bytes(yaml.safe_dump(existing_yaml)))
            galaxy_obj.truncate()

    # Create a file with +x in the collection so we can test the permissions
    execute_path = os.path.join(collection_path, 'runme.sh')
    with open(execute_path, mode='wb') as fd:
        fd.write(b"echo hi")
    os.chmod(execute_path, os.stat(execute_path).st_mode | stat.S_IEXEC)

    call_galaxy_cli(['build', collection_path, '--output-path', test_dir])

    collection_tar = os.path.join(test_dir, '%s-%s-0.1.0.tar.gz' % (namespace, collection))
    return to_bytes(collection_path), to_bytes(collection_tar)


@pytest.fixture()
def galaxy_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(None, 'test_server', 'https://galaxy.ansible.com')
    return galaxy_api


def test_build_requirement_from_path(collection_artifact):
    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    actual = Requirement.from_dir_path_as_unknown(collection_artifact[0], concrete_artifact_cm)

    assert actual.namespace == u'ansible_namespace'
    assert actual.name == u'collection'
    assert actual.src == collection_artifact[0]
    assert actual.ver == u'0.1.0'


@pytest.mark.parametrize('version', ['1.1.1', '1.1.0', '1.0.0'])
def test_build_requirement_from_path_with_manifest(version, collection_artifact):
    manifest_path = os.path.join(collection_artifact[0], b'MANIFEST.json')
    manifest_value = json.dumps({
        'collection_info': {
            'namespace': 'namespace',
            'name': 'name',
            'version': version,
            'dependencies': {
                'ansible_namespace.collection': '*'
            }
        }
    })
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(manifest_value))

    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    actual = Requirement.from_dir_path_as_unknown(collection_artifact[0], concrete_artifact_cm)

    # While the folder name suggests a different collection, we treat MANIFEST.json as the source of truth.
    assert actual.namespace == u'namespace'
    assert actual.name == u'name'
    assert actual.src == collection_artifact[0]
    assert actual.ver == to_text(version)


def test_build_requirement_from_path_invalid_manifest(collection_artifact):
    manifest_path = os.path.join(collection_artifact[0], b'MANIFEST.json')
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(b"not json")

    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)

    expected = "Collection tar file member MANIFEST.json does not contain a valid json string."
    with pytest.raises(AnsibleError, match=expected):
        Requirement.from_dir_path_as_unknown(collection_artifact[0], concrete_artifact_cm)


def test_build_artifact_from_path_no_version(collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    # a collection artifact should always contain a valid version
    manifest_path = os.path.join(collection_artifact[0], b'MANIFEST.json')
    manifest_value = json.dumps({
        'collection_info': {
            'namespace': 'namespace',
            'name': 'name',
            'version': '',
            'dependencies': {}
        }
    })
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(manifest_value))

    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)

    expected = (
        '^Collection metadata file `.*` at `.*` is expected to have a valid SemVer '
        'version value but got {empty_unicode_string!r}$'.
        format(empty_unicode_string=u'')
    )
    with pytest.raises(AnsibleError, match=expected):
        Requirement.from_dir_path_as_unknown(collection_artifact[0], concrete_artifact_cm)


def test_build_requirement_from_path_no_version(collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    # version may be falsey/arbitrary strings for collections in development
    manifest_path = os.path.join(collection_artifact[0], b'galaxy.yml')
    metadata = {
        'authors': ['Ansible'],
        'readme': 'README.md',
        'namespace': 'namespace',
        'name': 'name',
        'version': '',
        'dependencies': {},
    }
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(yaml.safe_dump(metadata)))

    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    actual = Requirement.from_dir_path_as_unknown(collection_artifact[0], concrete_artifact_cm)

    # While the folder name suggests a different collection, we treat MANIFEST.json as the source of truth.
    assert actual.namespace == u'namespace'
    assert actual.name == u'name'
    assert actual.src == collection_artifact[0]
    assert actual.ver == u'*'


def test_build_requirement_from_tar(collection_artifact):
    tmp_path = os.path.join(os.path.split(collection_artifact[1])[0], b'temp')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)

    actual = Requirement.from_requirement_dict({'name': to_text(collection_artifact[1])}, concrete_artifact_cm)

    assert actual.namespace == u'ansible_namespace'
    assert actual.name == u'collection'
    assert actual.src == to_text(collection_artifact[1])
    assert actual.ver == u'0.1.0'


def test_build_requirement_from_tar_fail_not_tar(tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    test_file = os.path.join(test_dir, b'fake.tar.gz')
    with open(test_file, 'wb') as test_obj:
        test_obj.write(b"\x00\x01\x02\x03")

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    expected = "Collection artifact at '%s' is not a valid tar file." % to_native(test_file)
    with pytest.raises(AnsibleError, match=expected):
        Requirement.from_requirement_dict({'name': to_text(test_file)}, concrete_artifact_cm)


def test_build_requirement_from_tar_no_manifest(tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = to_bytes(json.dumps(
        {
            'files': [],
            'format': 1,
        }
    ))

    tar_path = os.path.join(test_dir, b'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('FILES.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    expected = "Collection at '%s' does not contain the required file MANIFEST.json." % to_native(tar_path)
    with pytest.raises(AnsibleError, match=expected):
        Requirement.from_requirement_dict({'name': to_text(tar_path)}, concrete_artifact_cm)


def test_build_requirement_from_tar_no_files(tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = to_bytes(json.dumps(
        {
            'collection_info': {},
        }
    ))

    tar_path = os.path.join(test_dir, b'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    with pytest.raises(KeyError, match='namespace'):
        Requirement.from_requirement_dict({'name': to_text(tar_path)}, concrete_artifact_cm)


def test_build_requirement_from_tar_invalid_manifest(tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = b"not a json"

    tar_path = os.path.join(test_dir, b'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    expected = "Collection tar file member MANIFEST.json does not contain a valid json string."
    with pytest.raises(AnsibleError, match=expected):
        Requirement.from_requirement_dict({'name': to_text(tar_path)}, concrete_artifact_cm)


def test_build_requirement_from_name(galaxy_server, monkeypatch, tmp_path_factory):
    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['2.1.9', '2.1.10']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_version_metadata = MagicMock(
        namespace='namespace', name='collection',
        version='2.1.10', artifact_sha256='', dependencies={}
    )
    monkeypatch.setattr(api.GalaxyAPI, 'get_collection_version_metadata', mock_version_metadata)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    collections = ['namespace.collection']
    requirements_file = None

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', collections[0]])
    requirements = cli._require_one_of_collections_requirements(
        collections, requirements_file, artifacts_manager=concrete_artifact_cm
    )['collections']
    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, True, False, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.ver == u'2.1.10'
    assert actual.src == galaxy_server

    assert mock_get_versions.call_count == 1
    assert mock_get_versions.mock_calls[0][1] == ('namespace', 'collection')


def test_build_requirement_from_name_with_prerelease(galaxy_server, monkeypatch, tmp_path_factory):
    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['1.0.1', '2.0.1-beta.1', '2.0.1']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.1', None, None, {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection'], None, artifacts_manager=concrete_artifact_cm
    )['collections']
    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, True, False, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.1'

    assert mock_get_versions.call_count == 1
    assert mock_get_versions.mock_calls[0][1] == ('namespace', 'collection')


def test_build_requirment_from_name_with_prerelease_explicit(galaxy_server, monkeypatch, tmp_path_factory):
    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['1.0.1', '2.0.1-beta.1', '2.0.1']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.1-beta.1', None, None,
                                                               {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:2.0.1-beta.1'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:2.0.1-beta.1'], None, artifacts_manager=concrete_artifact_cm
    )['collections']
    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, True, False, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.1-beta.1'

    assert mock_get_info.call_count == 1
    assert mock_get_info.mock_calls[0][1] == ('namespace', 'collection', '2.0.1-beta.1')


def test_build_requirement_from_name_second_server(galaxy_server, monkeypatch, tmp_path_factory):
    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['1.0.1', '1.0.2', '1.0.3']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '1.0.3', None, None, {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    broken_server = copy.copy(galaxy_server)
    broken_server.api_server = 'https://broken.com/'
    mock_version_list = MagicMock()
    mock_version_list.return_value = []
    monkeypatch.setattr(broken_server, 'get_collection_versions', mock_version_list)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:>1.0.1'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:>1.0.1'], None, artifacts_manager=concrete_artifact_cm
    )['collections']
    actual = collection._resolve_depenency_map(
        requirements, [broken_server, galaxy_server], concrete_artifact_cm, None, True, False, False
    )['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'1.0.3'

    assert mock_version_list.call_count == 1
    assert mock_version_list.mock_calls[0][1] == ('namespace', 'collection')

    assert mock_get_versions.call_count == 1
    assert mock_get_versions.mock_calls[0][1] == ('namespace', 'collection')


def test_build_requirement_from_name_missing(galaxy_server, monkeypatch, tmp_path_factory):
    mock_open = MagicMock()
    mock_open.return_value = []

    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_open)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:>1.0.1'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    expected = "Failed to resolve the requested dependencies map. Could not satisfy the following requirements:\n* namespace.collection:* (direct request)"
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection._resolve_depenency_map(requirements, [galaxy_server, galaxy_server], concrete_artifact_cm, None, False, True, False)


def test_build_requirement_from_name_401_unauthorized(galaxy_server, monkeypatch, tmp_path_factory):
    mock_open = MagicMock()
    mock_open.side_effect = api.GalaxyError(urllib_error.HTTPError('https://galaxy.server.com', 401, 'msg', {},
                                                                   StringIO()), "error")

    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_open)

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:>1.0.1'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    expected = "error (HTTP Code: 401, Message: msg)"
    with pytest.raises(api.GalaxyError, match=re.escape(expected)):
        collection._resolve_depenency_map(requirements, [galaxy_server, galaxy_server], concrete_artifact_cm, None, False, False, False)


def test_build_requirement_from_name_single_version(galaxy_server, monkeypatch, tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    multi_api_proxy = collection.galaxy_api_proxy.MultiGalaxyAPIProxy([galaxy_server], concrete_artifact_cm)
    dep_provider = dependency_resolution.providers.CollectionDependencyProvider(apis=multi_api_proxy, concrete_artifacts_manager=concrete_artifact_cm)

    matches = RequirementCandidates()
    mock_find_matches = MagicMock(side_effect=matches.func_wrapper(dep_provider.find_matches), autospec=True)
    monkeypatch.setattr(dependency_resolution.providers.CollectionDependencyProvider, 'find_matches', mock_find_matches)

    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['2.0.0']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.0', None, None,
                                                               {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:==2.0.0'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:==2.0.0'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.0'
    assert [c.ver for c in matches.candidates] == [u'2.0.0']

    assert mock_get_info.call_count == 1
    assert mock_get_info.mock_calls[0][1] == ('namespace', 'collection', '2.0.0')


def test_build_requirement_from_name_multiple_versions_one_match(galaxy_server, monkeypatch, tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    multi_api_proxy = collection.galaxy_api_proxy.MultiGalaxyAPIProxy([galaxy_server], concrete_artifact_cm)
    dep_provider = dependency_resolution.providers.CollectionDependencyProvider(apis=multi_api_proxy, concrete_artifacts_manager=concrete_artifact_cm)

    matches = RequirementCandidates()
    mock_find_matches = MagicMock(side_effect=matches.func_wrapper(dep_provider.find_matches), autospec=True)
    monkeypatch.setattr(dependency_resolution.providers.CollectionDependencyProvider, 'find_matches', mock_find_matches)

    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['2.0.0', '2.0.1', '2.0.2']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.1', None, None,
                                                               {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:>=2.0.1,<2.0.2'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:>=2.0.1,<2.0.2'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.1'
    assert [c.ver for c in matches.candidates] == [u'2.0.1']

    assert mock_get_versions.call_count == 1
    assert mock_get_versions.mock_calls[0][1] == ('namespace', 'collection')

    assert mock_get_info.call_count == 1
    assert mock_get_info.mock_calls[0][1] == ('namespace', 'collection', '2.0.1')


def test_build_requirement_from_name_multiple_version_results(galaxy_server, monkeypatch, tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    multi_api_proxy = collection.galaxy_api_proxy.MultiGalaxyAPIProxy([galaxy_server], concrete_artifact_cm)
    dep_provider = dependency_resolution.providers.CollectionDependencyProvider(apis=multi_api_proxy, concrete_artifacts_manager=concrete_artifact_cm)

    matches = RequirementCandidates()
    mock_find_matches = MagicMock(side_effect=matches.func_wrapper(dep_provider.find_matches), autospec=True)
    monkeypatch.setattr(dependency_resolution.providers.CollectionDependencyProvider, 'find_matches', mock_find_matches)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.5', None, None, {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['1.0.1', '1.0.2', '1.0.3']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_versions.return_value = ['2.0.0', '2.0.1', '2.0.2', '2.0.3', '2.0.4', '2.0.5']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:!=2.0.2'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:!=2.0.2'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    actual = collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.5'
    # should be ordered latest to earliest
    assert [c.ver for c in matches.candidates] == [u'2.0.5', u'2.0.4', u'2.0.3', u'2.0.1', u'2.0.0']

    assert mock_get_versions.call_count == 1
    assert mock_get_versions.mock_calls[0][1] == ('namespace', 'collection')


def test_candidate_with_conflict(monkeypatch, tmp_path_factory, galaxy_server):

    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.5', None, None, {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['2.0.5']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:!=2.0.5'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:!=2.0.5'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    expected = "Failed to resolve the requested dependencies map. Could not satisfy the following requirements:\n"
    expected += "* namespace.collection:!=2.0.5 (direct request)"
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False)


def test_dep_candidate_with_conflict(monkeypatch, tmp_path_factory, galaxy_server):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    mock_get_info_return = [
        api.CollectionVersionMetadata('parent', 'collection', '2.0.5', None, None, {'namespace.collection': '!=1.0.0'}),
        api.CollectionVersionMetadata('namespace', 'collection', '1.0.0', None, None, {}),
    ]
    mock_get_info = MagicMock(side_effect=mock_get_info_return)
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    mock_get_versions = MagicMock(side_effect=[['2.0.5'], ['1.0.0']])
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'parent.collection:2.0.5'])
    requirements = cli._require_one_of_collections_requirements(
        ['parent.collection:2.0.5'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    expected = "Failed to resolve the requested dependencies map. Could not satisfy the following requirements:\n"
    expected += "* namespace.collection:!=1.0.0 (dependency of parent.collection:2.0.5)"
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        collection._resolve_depenency_map(requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False)


def test_install_installed_collection(monkeypatch, tmp_path_factory, galaxy_server):

    mock_installed_collections = MagicMock(return_value=[Candidate('namespace.collection', '1.2.3', None, 'dir')])

    monkeypatch.setattr(collection, 'find_existing_collections', mock_installed_collections)

    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '1.2.3', None, None, {})
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    mock_get_versions = MagicMock(return_value=['1.2.3', '1.3.0'])
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection'])
    cli.run()

    expected = "Nothing to do. All requested collections are already installed. If you want to reinstall them, consider using `--force`."
    assert mock_display.mock_calls[1][1][0] == expected


def test_install_collection(collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    collection_tar = collection_artifact[1]

    temp_path = os.path.join(os.path.split(collection_tar)[0], b'temp')
    os.makedirs(temp_path)
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)

    output_path = os.path.join(os.path.split(collection_tar)[0])
    collection_path = os.path.join(output_path, b'ansible_namespace', b'collection')
    os.makedirs(os.path.join(collection_path, b'delete_me'))  # Create a folder to verify the install cleans out the dir

    candidate = Candidate('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file')
    collection.install(candidate, to_text(output_path), concrete_artifact_cm)

    # Ensure the temp directory is empty, nothing is left behind
    assert os.listdir(temp_path) == []

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    assert stat.S_IMODE(os.stat(os.path.join(collection_path, b'plugins')).st_mode) == 0o0755
    assert stat.S_IMODE(os.stat(os.path.join(collection_path, b'README.md')).st_mode) == 0o0644
    assert stat.S_IMODE(os.stat(os.path.join(collection_path, b'runme.sh')).st_mode) == 0o0755

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" \
        % to_text(collection_path)
    assert mock_display.mock_calls[1][1][0] == "ansible_namespace.collection:0.1.0 was installed successfully"


def test_install_collection_with_download(galaxy_server, collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    shutil.rmtree(collection_path)

    collections_dir = ('%s' % os.path.sep).join(to_text(collection_path).split('%s' % os.path.sep)[:-2])

    temp_path = os.path.join(os.path.split(collection_tar)[0], b'temp')
    os.makedirs(temp_path)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)

    mock_download = MagicMock()
    mock_download.return_value = collection_tar
    monkeypatch.setattr(concrete_artifact_cm, 'get_galaxy_artifact_path', mock_download)

    req = Requirement('ansible_namespace.collection', '0.1.0', 'https://downloadme.com', 'galaxy')
    collection.install(req, to_text(collections_dir), concrete_artifact_cm)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" \
        % to_text(collection_path)
    assert mock_display.mock_calls[1][1][0] == "ansible_namespace.collection:0.1.0 was installed successfully"

    assert mock_download.call_count == 1
    assert mock_download.mock_calls[0][1][0].src == 'https://downloadme.com'
    assert mock_download.mock_calls[0][1][0].type == 'galaxy'


def test_install_collections_from_tar(collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    temp_path = os.path.split(collection_tar)[0]
    shutil.rmtree(collection_path)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)

    requirements = [Requirement('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file')]
    collection.install_collections(requirements, to_text(temp_path), [], False, False, False, False, False, False, concrete_artifact_cm)

    assert os.path.isdir(collection_path)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    with open(os.path.join(collection_path, b'MANIFEST.json'), 'rb') as manifest_obj:
        actual_manifest = json.loads(to_text(manifest_obj.read()))

    assert actual_manifest['collection_info']['namespace'] == 'ansible_namespace'
    assert actual_manifest['collection_info']['name'] == 'collection'
    assert actual_manifest['collection_info']['version'] == '0.1.0'

    # Filter out the progress cursor display calls.
    display_msgs = [m[1][0] for m in mock_display.mock_calls if 'newline' not in m[2] and len(m[1]) == 1]
    assert len(display_msgs) == 4
    assert display_msgs[0] == "Process install dependency map"
    assert display_msgs[1] == "Starting collection install process"
    assert display_msgs[2] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" % to_text(collection_path)


def test_install_collections_existing_without_force(collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    temp_path = os.path.split(collection_tar)[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)

    assert os.path.isdir(collection_path)

    requirements = [Requirement('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file')]
    collection.install_collections(requirements, to_text(temp_path), [], False, False, False, False, False, False, concrete_artifact_cm)

    assert os.path.isdir(collection_path)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'README.md', b'docs', b'galaxy.yml', b'playbooks', b'plugins', b'roles', b'runme.sh']

    # Filter out the progress cursor display calls.
    display_msgs = [m[1][0] for m in mock_display.mock_calls if 'newline' not in m[2] and len(m[1]) == 1]
    assert len(display_msgs) == 1

    assert display_msgs[0] == 'Nothing to do. All requested collections are already installed. If you want to reinstall them, consider using `--force`.'

    for msg in display_msgs:
        assert 'WARNING' not in msg


def test_install_missing_metadata_warning(collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    temp_path = os.path.split(collection_tar)[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    for file in [b'MANIFEST.json', b'galaxy.yml']:
        b_path = os.path.join(collection_path, file)
        if os.path.isfile(b_path):
            os.unlink(b_path)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)
    requirements = [Requirement('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file')]
    collection.install_collections(requirements, to_text(temp_path), [], False, False, False, False, False, False, concrete_artifact_cm)

    display_msgs = [m[1][0] for m in mock_display.mock_calls if 'newline' not in m[2] and len(m[1]) == 1]

    assert 'WARNING' in display_msgs[0]


# Makes sure we don't get stuck in some recursive loop
@pytest.mark.parametrize('collection_artifact', [
    {'ansible_namespace.collection': '>=0.0.1'},
], indirect=True)
def test_install_collection_with_circular_dependency(collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    temp_path = os.path.split(collection_tar)[0]
    shutil.rmtree(collection_path)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)
    requirements = [Requirement('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file')]
    collection.install_collections(requirements, to_text(temp_path), [], False, False, False, False, False, False, concrete_artifact_cm)

    assert os.path.isdir(collection_path)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    with open(os.path.join(collection_path, b'MANIFEST.json'), 'rb') as manifest_obj:
        actual_manifest = json.loads(to_text(manifest_obj.read()))

    assert actual_manifest['collection_info']['namespace'] == 'ansible_namespace'
    assert actual_manifest['collection_info']['name'] == 'collection'
    assert actual_manifest['collection_info']['version'] == '0.1.0'

    # Filter out the progress cursor display calls.
    display_msgs = [m[1][0] for m in mock_display.mock_calls if 'newline' not in m[2] and len(m[1]) == 1]
    assert len(display_msgs) == 4
    assert display_msgs[0] == "Process install dependency map"
    assert display_msgs[1] == "Starting collection install process"
    assert display_msgs[2] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" % to_text(collection_path)
    assert display_msgs[3] == "ansible_namespace.collection:0.1.0 was installed successfully"
