# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.filter.core import to_uuid,parse_semver,SEMVER_VALID_KEYS
from ansible.errors import AnsibleFilterError


UUID_DEFAULT_NAMESPACE_TEST_CASES = (
    ('example.com', 'ae780c3a-a3ab-53c2-bfb4-098da300b3fe'),
    ('test.example', '8e437a35-c7c5-50ea-867c-5c254848dbc2'),
    ('café.example', '8a99d6b1-fb8f-5f78-af86-879768589f56'),
)

UUID_TEST_CASES = (
    ('361E6D51-FAEC-444A-9079-341386DA8E2E', 'example.com', 'ae780c3a-a3ab-53c2-bfb4-098da300b3fe'),
    ('361E6D51-FAEC-444A-9079-341386DA8E2E', 'test.example', '8e437a35-c7c5-50ea-867c-5c254848dbc2'),
    ('11111111-2222-3333-4444-555555555555', 'example.com', 'e776faa5-5299-55dc-9057-7a00e6be2364'),
)


@pytest.mark.parametrize('value, expected', UUID_DEFAULT_NAMESPACE_TEST_CASES)
def test_to_uuid_default_namespace(value, expected):
    assert expected == to_uuid(value)


@pytest.mark.parametrize('namespace, value, expected', UUID_TEST_CASES)
def test_to_uuid(namespace, value, expected):
    assert expected == to_uuid(value, namespace=namespace)


def test_to_uuid_invalid_namespace():
    with pytest.raises(AnsibleFilterError) as e:
        to_uuid('example.com', namespace='11111111-2222-3333-4444-555555555')
    assert 'Invalid value' in to_native(e.value)


SEMVER_VALID_VSTRINGS = (
    ('0.0.4'),
    ('1.2.3'),
    ('10.20.30'),
    ('1.1.2-prerelease+meta'),
    ('1.1.2+meta'),
    ('1.1.2+meta-valid'),
    ('1.0.0-alpha'),
    ('1.0.0-beta'),
    ('1.0.0-alpha.beta'),
    ('1.0.0-alpha.beta.1'),
    ('1.0.0-alpha.1'),
    ('1.0.0-alpha0.valid'),
    ('1.0.0-alpha.0valid'),
    ('1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay'),
    ('1.0.0-rc.1+build.1'),
    ('2.0.0-rc.1+build.123'),
    ('1.2.3-beta'),
    ('10.2.3-DEV-SNAPSHOT'),
    ('1.2.3-SNAPSHOT-123'),
    ('1.0.0'),
    ('2.0.0'),
    ('1.1.7'),
    ('2.0.0+build.1848'),
    ('2.0.1-alpha.1227'),
    ('1.0.0-alpha+beta'),
    ('1.2.3----RC-SNAPSHOT.12.9.1--.12+788'),
    ('1.2.3----R-S.12.9.1--.12+meta'),
    ('1.2.3----RC-SNAPSHOT.12.9.1--.12'),
    ('1.0.0+0.build.1-rc.10000aaa-kk-0.1'),
    ('99999999999999999999999.999999999999999999.99999999999999999'),
    ('1.0.0-0A.is.legal')
)

SEMVER_VALID_TEST_CASES=(
    (   '0.0.4',
        {   'buildmetadata': (),
            'major': 0,
            'minor': 0,
            'patch': 4,
            'prerelease': ()}),
    (   '1.2.3',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ()}),
    (   '10.20.30',
        {   'buildmetadata': (),
            'major': 10,
            'minor': 20,
            'patch': 30,
            'prerelease': ()}),
    (   '1.1.2-prerelease+meta',
        {   'buildmetadata': ('meta',),
            'major': 1,
            'minor': 1,
            'patch': 2,
            'prerelease': ('prerelease',)}),
    (   '1.1.2+meta',
        {   'buildmetadata': ('meta',),
            'major': 1,
            'minor': 1,
            'patch': 2,
            'prerelease': ()}),
    (   '1.1.2+meta-valid',
        {   'buildmetadata': ('meta-valid',),
            'major': 1,
            'minor': 1,
            'patch': 2,
            'prerelease': ()}),
    (   '1.0.0-alpha',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha',)}),
    (   '1.0.0-beta',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('beta',)}),
    (   '1.0.0-alpha.beta',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha', 'beta')}),
    (   '1.0.0-alpha.beta.1',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha', 'beta', 1)}),
    (   '1.0.0-alpha.1',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha', 1)}),
    (   '1.0.0-alpha0.valid',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha0', 'valid')}),
    (   '1.0.0-alpha.0valid',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha', '0valid')}),
    (   '1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',
        {   'buildmetadata': ('build', '1-aef', '1-its-okay'),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha-a', 'b-c-somethinglong')}),
    (   '1.0.0-rc.1+build.1',
        {   'buildmetadata': ('build', 1),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('rc', 1)}),
    (   '2.0.0-rc.1+build.123',
        {   'buildmetadata': ('build', 123),
            'major': 2,
            'minor': 0,
            'patch': 0,
            'prerelease': ('rc', 1)}),
    (   '1.2.3-beta',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ('beta',)}),
    (   '10.2.3-DEV-SNAPSHOT',
        {   'buildmetadata': (),
            'major': 10,
            'minor': 2,
            'patch': 3,
            'prerelease': ('DEV-SNAPSHOT',)}),
    (   '1.2.3-SNAPSHOT-123',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ('SNAPSHOT-123',)}),
    (   '1.0.0',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ()}),
    (   '2.0.0',
        {   'buildmetadata': (),
            'major': 2,
            'minor': 0,
            'patch': 0,
            'prerelease': ()}),
    (   '1.1.7',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 1,
            'patch': 7,
            'prerelease': ()}),
    (   '2.0.0+build.1848',
        {   'buildmetadata': ('build', 1848),
            'major': 2,
            'minor': 0,
            'patch': 0,
            'prerelease': ()}),
    (   '2.0.1-alpha.1227',
        {   'buildmetadata': (),
            'major': 2,
            'minor': 0,
            'patch': 1,
            'prerelease': ('alpha', 1227)}),
    (   '1.0.0-alpha+beta',
        {   'buildmetadata': ('beta',),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('alpha',)}),
    (   '1.2.3----RC-SNAPSHOT.12.9.1--.12+788',
        {   'buildmetadata': (788,),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ('---RC-SNAPSHOT', 12, 9, '1--', 12)}),
    (   '1.2.3----R-S.12.9.1--.12+meta',
        {   'buildmetadata': ('meta',),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ('---R-S', 12, 9, '1--', 12)}),
    (   '1.2.3----RC-SNAPSHOT.12.9.1--.12',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 2,
            'patch': 3,
            'prerelease': ('---RC-SNAPSHOT', 12, 9, '1--', 12)}),
    (   '1.0.0+0.build.1-rc.10000aaa-kk-0.1',
        {   'buildmetadata': (0, 'build', '1-rc', '10000aaa-kk-0', 1),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ()}),
    (   '99999999999999999999999.999999999999999999.99999999999999999',
        {   'buildmetadata': (),
            'major': 99999999999999999999999,
            'minor': 999999999999999999,
            'patch': 99999999999999999,
            'prerelease': ()}),
    (   '1.0.0-0A.is.legal',
        {   'buildmetadata': (),
            'major': 1,
            'minor': 0,
            'patch': 0,
            'prerelease': ('0A', 'is', 'legal')})
        )

@pytest.mark.parametrize('vstring, expected', SEMVER_VALID_TEST_CASES)
def test_parse_semver_valid_vstring(vstring, expected):
    parsed_semver = parse_semver(vstring)
    for key in SEMVER_VALID_KEYS:
        assert expected[key] == parsed_semver[key]


SEMVER_INVALID_VSTRINGS = (
    (1),  # Deliberatly a numeric 1 as this is not supported
    ('1'),
    ('1.2'),
    ('1.2.3-0123'),
    ('1.2.3-0123.0123'),
    ('1.1.2+.123'),
    ('+invalid'),
    ('-invalid'),
    ('-invalid+invalid'),
    ('-invalid.01'),
    ('alpha'),
    ('alpha.beta'),
    ('alpha.beta.1'),
    ('alpha.1'),
    ('alpha+beta'),
    ('alpha_beta'),
    ('alpha.'),
    ('alpha..'),
    ('beta'),
    ('1.0.0-alpha_beta'),
    ('-alpha.'),
    ('1.0.0-alpha..'),
    ('1.0.0-alpha..1'),
    ('1.0.0-alpha...1'),
    ('1.0.0-alpha....1'),
    ('1.0.0-alpha.....1'),
    ('1.0.0-alpha......1'),
    ('1.0.0-alpha.......1'),
    ('01.1.1'),
    ('1.01.1'),
    ('1.1.01'),
    ('1.2'),
    ('1.2.3.DEV'),
    ('1.2-SNAPSHOT'),
    ('1.2.31.2.3----RC-SNAPSHOT.12.09.1--..12+788'),
    ('1.2-RC-SNAPSHOT'),
    ('-1.0.3-gamma+b7718'),
    ('+justmeta'),
    ('9.8.7+meta+meta'),
    ('9.8.7-whatever+meta+meta'),
    ('99999999999999999999999.999999999999999999.99999999999999999----RC-SNAPSHOT.12.09.1--------------------------------..12')
)

@pytest.mark.parametrize('vstring', SEMVER_INVALID_VSTRINGS)
def test_parse_semver_invalid_vstring(vstring):
    with pytest.raises(AnsibleFilterError) as e:
        parse_semver(vstring)
    assert 'Invalid value' in to_native(e.value)

@pytest.mark.parametrize('vstring', SEMVER_VALID_VSTRINGS)
def test_parse_semver_valid_vstring_invalid_key(vstring,keys=['stuff']):
    with pytest.raises(AnsibleFilterError) as e:
        parse_semver(vstring,keys=keys)
    assert 'Invalid key' in to_native(e.value)
