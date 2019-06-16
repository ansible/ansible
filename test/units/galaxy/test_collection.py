# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import tempfile

from units.compat.mock import MagicMock

from ansible.errors import AnsibleError
from ansible.galaxy import collection
from ansible.utils.display import Display


def test_build_collection_no_galaxy_yaml():
    expected = "The collection galaxy.yml path '/fake/path/galaxy.yml' does not exist."

    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection('/fake/path', 'output', False)


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
