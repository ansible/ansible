# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import pytest
import tarfile

from io import BytesIO, StringIO
from units.compat.mock import MagicMock

import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleError
from ansible.galaxy import collection
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils import context_objects as co


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


def artifact_versions_json(namespace, name, versions, server):
    results = []
    for version in versions:
        results.append({
            'href': '%s/api/v2/%s/%s/versions/%s/' % (server, namespace, name, version),
            'version': version,
        })

    json_str = json.dumps({
        'count': len(versions),
        'next': None,
        'previous': None,
        'results': results
    })
    return to_text(json_str)


@pytest.fixture()
def collection_artifact(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    namespace = 'ansible_namespace'
    collection = 'collection'

    skeleton_path = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'collection_skeleton')
    collection_path = os.path.join(test_dir, namespace, collection)

    call_galaxy_cli(['init', '%s.%s' % (namespace, collection), '-c', '--init-path', test_dir,
                     '--collection-skeleton', skeleton_path])
    call_galaxy_cli(['build', collection_path, '--output-path', test_dir])

    collection_tar = os.path.join(test_dir, '%s-%s-0.1.0.tar.gz' % (namespace, collection))
    return collection_path, collection_tar


def test_build_requirement_from_path(collection_artifact):
    actual = collection.CollectionRequirement.from_path(collection_artifact[0], True, True)

    assert actual.namespace == u'ansible_namespace'
    assert actual.name == u'collection'
    assert actual.path == collection_artifact[0]
    assert actual.source is None
    assert actual.skip is True
    assert actual.versions == set([u'*'])
    assert actual.latest_version == u'*'
    assert actual.dependencies == {}


def test_build_requirement_from_path_with_manifest(collection_artifact):
    manifest_path = os.path.join(collection_artifact[0], 'MANIFEST.json')
    manifest_value = json.dumps({
        'collection_info': {
            'namespace': 'namespace',
            'name': 'name',
            'version': '1.1.1',
            'dependencies': {
                'ansible_namespace.collection': '*'
            }
        }
    })
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(manifest_value))

    actual = collection.CollectionRequirement.from_path(collection_artifact[0], True, True)

    # While the folder name suggests a different collection, we treat MANIFEST.json as the source of truth.
    assert actual.namespace == u'namespace'
    assert actual.name == u'name'
    assert actual.path == collection_artifact[0]
    assert actual.source is None
    assert actual.skip is True
    assert actual.versions == set([u'1.1.1'])
    assert actual.latest_version == u'1.1.1'
    assert actual.dependencies == {'ansible_namespace.collection': '*'}


def test_build_requirement_from_path_invalid_manifest(collection_artifact):
    manifest_path = os.path.join(collection_artifact[0], 'MANIFEST.json')
    with open(manifest_path, 'wb') as manifest_obj:
        manifest_obj.write(b"not json")

    expected = "Collection file at '%s' is not a valid json string." % to_native(manifest_path)
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_path(collection_artifact[0], True, True)


def test_build_requirement_from_tar(collection_artifact):
    actual = collection.CollectionRequirement.from_tar(collection_artifact[1], True, True)

    assert actual.namespace == u'ansible_namespace'
    assert actual.name == u'collection'
    assert actual.path == collection_artifact[1]
    assert actual.source is None
    assert actual.skip is False
    assert actual.versions == set([u'0.1.0'])
    assert actual.latest_version == u'0.1.0'
    assert actual.dependencies == {}


def test_build_requirement_from_tar_fail_not_tar(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    test_file = os.path.join(test_dir, 'fake.tar.gz')
    with open(test_file, 'wb') as test_obj:
        test_obj.write(b"\x00\x01\x02\x03")

    expected = "Collection artifact at '%s' is not a valid tar file." % to_native(test_file)
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_tar(test_file, True, True)


def test_build_requirement_from_tar_no_manifest(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = to_bytes(json.dumps(
        {
            'files': [],
            'format': 1,
        }
    ))

    tar_path = os.path.join(test_dir, 'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('FILES.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = "Collection at '%s' does not contain the required file MANIFEST.json." % to_native(tar_path)
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_tar(tar_path, True, True)


def test_build_requirement_from_tar_no_files(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = to_bytes(json.dumps(
        {
            'collection_info': {},
        }
    ))

    tar_path = os.path.join(test_dir, 'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = "Collection at '%s' does not contain the required file FILES.json." % to_native(tar_path)
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_tar(tar_path, True, True)


def test_build_requirement_from_tar_invalid_manifest(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))

    json_data = b"not a json"

    tar_path = os.path.join(test_dir, 'ansible-collections.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(json_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(json_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = "Collection tar file MANIFEST.json is not a valid json string."
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_tar(tar_path, True, True)


def test_build_requirement_from_name(monkeypatch):
    galaxy_server = 'https://galaxy.ansible.com'
    json_str = artifact_versions_json('namespace', 'collection', ['2.1.9', '2.1.10'], galaxy_server)
    mock_open = MagicMock()
    mock_open.return_value = StringIO(json_str)
    monkeypatch.setattr(collection, 'open_url', mock_open)

    actual = collection.CollectionRequirement.from_name('namespace.collection', [galaxy_server], '*', True, True)

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.path is None
    assert actual.source == to_text(galaxy_server)
    assert actual.skip is False
    assert actual.versions == set([u'2.1.9', u'2.1.10'])
    assert actual.latest_version == u'2.1.10'
    assert actual.dependencies is None

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == u"%s/api/v2/collections/namespace/collection/versions/" % galaxy_server
    assert mock_open.mock_calls[0][2] == {'validate_certs': True}


def test_build_requirement_from_name_second_server(monkeypatch):
    galaxy_server = 'https://galaxy-dev.ansible.com'
    json_str = artifact_versions_json('namespace', 'collection', ['1.0.1', '1.0.2', '1.0.3'], galaxy_server)
    mock_open = MagicMock()
    mock_open.side_effect = (
        urllib_error.HTTPError('https://galaxy.server.com', 404, 'msg', {}, None),
        StringIO(json_str)
    )

    monkeypatch.setattr(collection, 'open_url', mock_open)

    actual = collection.CollectionRequirement.from_name('namespace.collection', ['https://broken.com/', galaxy_server],
                                                        '>1.0.1', False, True)

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.path is None
    assert actual.source == to_text(galaxy_server)
    assert actual.skip is False
    assert actual.versions == set([u'1.0.2', u'1.0.3'])
    assert actual.latest_version == u'1.0.3'
    assert actual.dependencies is None

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == u"https://broken.com/api/v2/collections/namespace/collection/versions/"
    assert mock_open.mock_calls[0][2] == {'validate_certs': False}
    assert mock_open.mock_calls[1][1][0] == u"%s/api/v2/collections/namespace/collection/versions/" % galaxy_server
    assert mock_open.mock_calls[1][2] == {'validate_certs': False}


def test_build_requirement_from_name_missing(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = urllib_error.HTTPError('https://galaxy.server.com', 404, 'msg', {}, None)

    monkeypatch.setattr(collection, 'open_url', mock_open)

    expected = "Failed to find collection namespace.collection:*"
    with pytest.raises(AnsibleError, match=expected):
        collection.CollectionRequirement.from_name('namespace.collection',
                                                   ['https://broken.com/', 'https://broken2.com'], '*', False, True)


def test_build_requirement_from_name_single_version(monkeypatch):
    galaxy_server = 'https://galaxy.ansible.com'
    json_str = artifact_json('namespace', 'collection', '2.0.0', {}, galaxy_server)
    mock_open = MagicMock()
    mock_open.return_value = StringIO(json_str)

    monkeypatch.setattr(collection, 'open_url', mock_open)

    actual = collection.CollectionRequirement.from_name('namespace.collection', [galaxy_server], '2.0.0', True, True)

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.path is None
    assert actual.source == to_text(galaxy_server)
    assert actual.skip is False
    assert actual.versions == set([u'2.0.0'])
    assert actual.latest_version == u'2.0.0'
    assert actual.dependencies == {}

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == u"%s/api/v2/collections/namespace/collection/versions/2.0.0/" \
        % galaxy_server
    assert mock_open.mock_calls[0][2] == {'validate_certs': True}


def test_build_requirement_from_name_multiple_versions_one_match(monkeypatch):
    galaxy_server = 'https://galaxy.ansible.com'
    json_str1 = artifact_versions_json('namespace', 'collection', ['2.0.0', '2.0.1', '2.0.2'], galaxy_server)
    json_str2 = artifact_json('namespace', 'collection', '2.0.1', {}, galaxy_server)
    mock_open = MagicMock()
    mock_open.side_effect = (StringIO(json_str1), StringIO(json_str2))

    monkeypatch.setattr(collection, 'open_url', mock_open)

    actual = collection.CollectionRequirement.from_name('namespace.collection', [galaxy_server], '>=2.0.1,<2.0.2',
                                                        True, True)

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.path is None
    assert actual.source == to_text(galaxy_server)
    assert actual.skip is False
    assert actual.versions == set([u'2.0.1'])
    assert actual.latest_version == u'2.0.1'
    assert actual.dependencies == {}

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == u"%s/api/v2/collections/namespace/collection/versions/" % galaxy_server
    assert mock_open.mock_calls[0][2] == {'validate_certs': True}
    assert mock_open.mock_calls[1][1][0] == u"%s/api/v2/collections/namespace/collection/versions/2.0.1/" \
        % galaxy_server
    assert mock_open.mock_calls[1][2] == {'validate_certs': True}


def test_build_requirement_from_name_multiple_version_results(monkeypatch):
    galaxy_server = 'https://galaxy-dev.ansible.com'

    json_str1 = json.dumps({
        'count': 6,
        'next': '%s/api/v2/collections/namespace/collection/versions/?page=2' % galaxy_server,
        'previous': None,
        'results': [
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.0/' % galaxy_server,
                'version': '2.0.0',
            },
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.1/' % galaxy_server,
                'version': '2.0.1',
            },
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.2/' % galaxy_server,
                'version': '2.0.2',
            },
        ]
    })
    json_str2 = json.dumps({
        'count': 6,
        'next': None,
        'previous': '%s/api/v2/collections/namespace/collection/versions/?page=1' % galaxy_server,
        'results': [
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.3/' % galaxy_server,
                'version': '2.0.3',
            },
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.4/' % galaxy_server,
                'version': '2.0.4',
            },
            {
                'href': '%s/api/v2/collections/namespace/collection/versions/2.0.5/' % galaxy_server,
                'version': '2.0.5',
            },
        ]
    })
    mock_open = MagicMock()
    mock_open.side_effect = (StringIO(to_text(json_str1)), StringIO(to_text(json_str2)))

    monkeypatch.setattr(collection, 'open_url', mock_open)

    actual = collection.CollectionRequirement.from_name('namespace.collection', [galaxy_server], '!=2.0.2',
                                                        True, True)

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.path is None
    assert actual.source == to_text(galaxy_server)
    assert actual.skip is False
    assert actual.versions == set([u'2.0.0', u'2.0.1', u'2.0.3', u'2.0.4', u'2.0.5'])
    assert actual.latest_version == u'2.0.5'
    assert actual.dependencies is None

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == u"%s/api/v2/collections/namespace/collection/versions/" % galaxy_server
    assert mock_open.mock_calls[0][2] == {'validate_certs': True}
    assert mock_open.mock_calls[1][1][0] == u"%s/api/v2/collections/namespace/collection/versions/?page=2" \
        % galaxy_server
    assert mock_open.mock_calls[1][2] == {'validate_certs': True}
