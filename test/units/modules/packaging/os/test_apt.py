import collections
import os
import sys

from ansible.compat.tests import mock
from ansible.compat.tests import unittest

try:
    from ansible.modules.packaging.os.apt import (
        expand_pkgspec_from_fnmatches,
    )
except:
    # Need some more module_utils work (porting urls.py) before we can test
    # modules.  So don't error out in this case.
    if sys.version_info[0] >= 3:
        pass


class AptExpandPkgspecTestCase(unittest.TestCase):

    def setUp(self):
        FakePackage = collections.namedtuple("Package", ("name",))
        self.fake_cache = [
            FakePackage("apt"),
            FakePackage("apt-utils"),
            FakePackage("not-selected"),
        ]

    def test_trivial(self):
        foo = ["apt"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, foo, self.fake_cache), foo)

    def test_version_wildcard(self):
        foo = ["apt=1.0*"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, foo, self.fake_cache), foo)

    def test_pkgname_wildcard_version_wildcard(self):
        foo = ["apt*=1.0*"]
        m_mock = mock.Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, foo, self.fake_cache),
            ['apt', 'apt-utils'])

    def test_pkgname_expands(self):
        foo = ["apt*"]
        m_mock = mock.Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, foo, self.fake_cache),
            ["apt", "apt-utils"])
