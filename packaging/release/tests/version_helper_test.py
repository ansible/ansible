from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from packaging.version import InvalidVersion
from versionhelper.version_helper import AnsibleVersionMunger


@pytest.mark.parametrize('version,revision,output_propname,expected', [
    ('2.5.0dev1', None, 'raw', '2.5.0dev1'),
    ('2.5.0', None, 'raw', '2.5.0'),
    ('2.5.0dev1', None, 'major_version', '2.5'),
    ('2.5.0', None, 'major_version', '2.5'),
    ('2.5.0dev1', None, 'base_version', '2.5.0'),
    ('2.5.0', None, 'base_version', '2.5.0'),
    ('2.5.0dev1', None, 'deb_version', '2.5.0~dev1'),
    ('2.5.0b1', None, 'deb_version', '2.5.0~b1'),
    ('2.5.0', None, 'deb_version', '2.5.0'),
    ('2.5.0dev1', None, 'deb_release', '1'),
    ('2.5.0b1', 2, 'deb_release', '2'),
    ('2.5.0dev1', None, 'rpm_release', '0.1.dev1'),
    ('2.5.0a1', None, 'rpm_release', '0.101.a1'),
    ('2.5.0b1', None, 'rpm_release', '0.201.b1'),
    ('2.5.0rc1', None, 'rpm_release', '0.1001.rc1'),
    ('2.5.0rc1', '0.99', 'rpm_release', '0.99.rc1'),
    ('2.5.0.rc.1', None, 'rpm_release', '0.1001.rc.1'),
    ('2.5.0', None, 'rpm_release', '1'),
    ('2.5.0', 2, 'rpm_release', '2'),
    ('2.5.0x1', None, None, InvalidVersion)
])
def test_output_values(version, revision, output_propname, expected):
    try:
        v = AnsibleVersionMunger(version, revision)
        assert getattr(v, output_propname) == expected
    except Exception as ex:
        if isinstance(expected, type):
            assert isinstance(ex, expected)
        else:
            raise
